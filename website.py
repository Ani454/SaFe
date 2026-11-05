"""SaFe's integrated website. Run with Flask or Gunicorn; see DEPLOYMENT.md."""
import functools,json,os,secrets,sqlite3
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from io import BytesIO
from flask import Flask,render_template,request,redirect,url_for,session,flash,abort,g,send_from_directory
from werkzeug.security import generate_password_hash,check_password_hash
from PIL import Image,UnidentifiedImageError
import store,pipeline,es_store,mistral_ai as ai
from ui_server import load_env
load_env()

def create_app(test_config=None):
    app=Flask(__name__)
    directory=Path(os.environ.get('SAFE_STORAGE','instance')); os.environ.setdefault('SAFE_DB',str(directory/'safe.db')); directory.mkdir(parents=True,exist_ok=True)
    secret=os.environ.get('SAFE_SECRET_KEY')
    if not secret:
        if os.environ.get('SAFE_ENV')=='production': raise RuntimeError('SAFE_SECRET_KEY is required in production.')
        p=directory/'session.key'
        if not p.exists(): p.write_text(secrets.token_hex(32)); p.chmod(0o600)
        secret=p.read_text()
    app.config.update(SECRET_KEY=secret,MAX_CONTENT_LENGTH=8*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('SAFE_ENV')=='production',UPLOAD_FOLDER=str(directory/'uploads'))
    if test_config: app.config.update(test_config)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True,exist_ok=True)
    store.init()
    with store.connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS login_attempts(email TEXT PRIMARY KEY,count INTEGER NOT NULL,updated REAL NOT NULL)')

    @app.before_request
    def before():
        g.user=None
        if session.get('user_id'):
            with store.connect() as c: g.user=c.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
        if 'csrf' not in session: session['csrf']=secrets.token_hex(32)
        if request.method=='POST' and not secrets.compare_digest(session['csrf'],request.form.get('csrf','')): abort(400,'Your form expired. Reload and try again.')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'; response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'; response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline' https://unpkg.com; script-src 'self' https://unpkg.com; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.context_processor
    def context(): return dict(csrf=session.get('csrf'),categories=ai.CATEGORIES,backend=es_store.backend(),uid=store.uid,label=lambda s:s.replace('_',' ').title())

    def login(fn):
        @functools.wraps(fn)
        def wrapped(*a,**k):
            if not g.user: return redirect(url_for('auth',mode='login'))
            return fn(*a,**k)
        return wrapped
    def admin(fn):
        @functools.wraps(fn)
        @login
        def wrapped(*a,**k):
            if g.user['role']!='admin': abort(403)
            return fn(*a,**k)
        return wrapped
    def text(name,limit=2000): return ai._text(request.form.get(name),name.replace('_',' ').title(),limit)
    def photo(required=False):
        f=request.files.get('photo')
        if not f or not f.filename:
            if required: raise ValueError('An after photo is required for completion review.')
            return None
        try:
            image=Image.open(f.stream)
            if image.format not in {'JPEG','PNG','WEBP'} or image.width*image.height>20000000: raise ValueError('Use a JPG, PNG, or WebP image under 20 megapixels.')
            image.load(); image.thumbnail((1800,1800)); image=image.convert('RGB')
            name=store.uid()+'.jpg'; image.save(Path(app.config['UPLOAD_FOLDER'])/name,'JPEG',quality=85)
            return name
        except (UnidentifiedImageError,OSError,Image.DecompressionBombError): raise ValueError('The photo could not be read. Use a valid JPG, PNG, or WebP image.')

    @app.errorhandler(ValueError)
    def invalid(e): return render_template('error.html',message=str(e)),400
    @app.errorhandler(ai.MistralError)
    def provider(e): return render_template('error.html',message=str(e).replace(' Sample previews are available without a key.','')),503
    @app.errorhandler(RuntimeError)
    def service(e): return render_template('error.html',message=str(e)),503
    @app.errorhandler(403)
    def forbidden(e): return render_template('error.html',message='You do not have permission to perform this action.'),403
    @app.errorhandler(404)
    def missing(e): return render_template('error.html',message='That page was not found.'),404
    @app.errorhandler(413)
    def large(e): return render_template('error.html',message='Upload is too large. Maximum request size is 8 MB.'),413

    @app.route('/auth/<mode>',methods=['GET','POST'])
    def auth(mode):
        if mode not in {'login','register'}: abort(404)
        if request.method=='POST':
            import time
            email=text('email',254).lower(); password=text('password',256)
            if '@' not in email or len(password)<12: raise ValueError('Use a valid email and a password of at least 12 characters.')
            with store.connect() as c:
                if mode=='register':
                    try: c.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',(store.uid(),email,text('name',80),generate_password_hash(password),'resident',store.now()))
                    except sqlite3.IntegrityError: raise ValueError('This email is unavailable. Try signing in.')
                attempt=c.execute('SELECT * FROM login_attempts WHERE email=?',(email,)).fetchone()
                if attempt and attempt['count']>=8 and time.time()-attempt['updated']<900: raise ValueError('Too many attempts. Try again in 15 minutes.')
                user=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if not user or not check_password_hash(user['password'],password):
                    c.execute('INSERT INTO login_attempts VALUES(?,1,?) ON CONFLICT(email) DO UPDATE SET count=CASE WHEN updated<? THEN 1 ELSE count+1 END,updated=excluded.updated',(email,time.time(),time.time()-900)); c.commit()
                    raise ValueError('Email or password is incorrect.')
                c.execute('DELETE FROM login_attempts WHERE email=?',(email,))
                session.clear(); session['user_id']=user['id']; session['csrf']=secrets.token_hex(32)
            return redirect(url_for('explore'))
        return render_template('auth.html',mode=mode)

    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('explore'))

    @app.get('/')
    def explore():
        with store.connect() as c: issues=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM issues')]
        category=request.args.get('category',''); status=request.args.get('status',''); since=request.args.get('since','')
        if since:
            try: datetime.strptime(since,'%Y-%m-%d')
            except ValueError: raise ValueError('Choose a valid date.')
        issues=[i for i in issues if (not category or i['category']==category) and (not status or i['status']==status) and (not since or i['created_at'][:10]>=since)]
        if request.args.get('distance'):
            lat,lon=store.coordinates(request.args.get('lat'),request.args.get('lon'))
            radius=float(request.args['distance'])
            if not 0<radius<=100000: raise ValueError('Distance must be between 1 and 100000 meters.')
            issues=[i for i in issues if store.distance(i['location'],{'lat':lat,'lon':lon})<=radius]
        issues.sort(key=lambda i:i['updated_at'],reverse=True)
        return render_template('explore.html',issues=[{k:v for k,v in i.items() if k not in {'reporters','report_texts','agency_draft'}} for i in issues])

    @app.route('/report',methods=['GET','POST'])
    @login
    def report():
        if request.method=='POST':
            lat,lon=store.coordinates(request.form.get('lat'),request.form.get('lon'))
            try:
                result=pipeline.submit(g.user['id'],text('description',6000),lat,lon,text('request_key',80),photo())
            except (ai.MistralError, RuntimeError, ai.ClarificationNeeded) as e:
                return render_template('report.html',error=str(e).replace(' Sample previews are available without a key.','')),503 if not isinstance(e,ai.ClarificationNeeded) else 422
            flash(result['message']); return redirect(url_for('issue',id=result['issue_id']))
        return render_template('report.html')

    @app.get('/issues/<id>')
    def issue(id):
        with store.connect() as c:
            d=store.get_issue(c,id)
            history=c.execute('SELECT * FROM events WHERE issue_id=? ORDER BY created_at',(id,)).fetchall()
            activities=c.execute('SELECT * FROM activities WHERE issue_id=? ORDER BY starts_at',(id,)).fetchall()
            contributions=c.execute('SELECT x.*,u.name FROM contributions x JOIN users u ON u.id=x.user_id WHERE issue_id=? ORDER BY created_at DESC',(id,)).fetchall()
            reports=c.execute('SELECT text,photo,created_at FROM reports WHERE issue_id=? ORDER BY created_at',(id,)).fetchall()
        return render_template('issue.html',issue=d,history=history,activities=activities,contributions=contributions,reports=reports)

    @app.route('/activities',methods=['GET','POST'])
    @login
    def activities():
        if request.method=='POST':
            with store.connect() as c:
                d=store.get_issue(c,text('issue_id',80))
                if d['category']!='illegal_dumping' or d['status']=='resolved': raise ValueError('Activities are available for open cleanup issues only. Agency repairs stay with professionals.')
                start=datetime.fromisoformat(text('starts_at',80))
                if start.tzinfo is None: start=start.replace(tzinfo=ZoneInfo('America/Los_Angeles'))
                if start<=datetime.now(timezone.utc): raise ValueError('Choose a future activity date and time.')
                capacity=int(text('capacity',5))
                if not 1<=capacity<=200: raise ValueError('Participant limit must be 1–200.')
                id=store.uid(); c.execute('INSERT INTO activities VALUES(?,?,?,?,?,?,?,?,?)',(id,d['issue_id'],g.user['id'],text('title',120),text('description'),start.isoformat(),text('meeting',300),capacity,store.now()))
                store.history(c,d['issue_id'],g.user['id'],'activity_created','Community activity scheduled.')
            return redirect(url_for('activity',id=id))
        with store.connect() as c:
            rows=c.execute('SELECT a.*,u.name,(SELECT count(*) FROM participants p WHERE p.activity_id=a.id) joined FROM activities a JOIN users u ON u.id=a.organizer ORDER BY starts_at').fetchall()
            issues=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM issues')]
        return render_template('activities.html',activities=rows,issues=[i for i in issues if i['category']=='illegal_dumping' and i['status']!='resolved'])

    @app.route('/activities/<id>',methods=['GET','POST'])
    @login
    def activity(id):
        with store.connect() as c:
            if request.method=='POST': c.execute('BEGIN IMMEDIATE')
            a=c.execute('SELECT * FROM activities WHERE id=?',(id,)).fetchone()
            if not a: abort(404)
            members=c.execute('SELECT u.id,u.name FROM participants p JOIN users u ON u.id=p.user_id WHERE p.activity_id=?',(id,)).fetchall()
            joined=any(m['id']==g.user['id'] for m in members)
            if request.method=='POST':
                if request.form.get('action')=='leave': c.execute('DELETE FROM participants WHERE activity_id=? AND user_id=?',(id,g.user['id']))
                elif request.form.get('action')=='join':
                    if not joined:
                        if datetime.fromisoformat(a['starts_at'])<=datetime.now(timezone.utc): raise ValueError('This activity has already started.')
                        if store.get_issue(c,a['issue_id'])['status']=='resolved': raise ValueError('This issue is resolved; joining is closed.')
                        if len(members)>=a['capacity']: raise ValueError('This activity is full.')
                        c.execute('INSERT INTO participants VALUES(?,?)',(id,g.user['id']))
                else: raise ValueError('Choose join or leave.')
                return redirect(url_for('activity',id=id))
        return render_template('activity.html',activity=a,members=members,joined=joined)

    @app.post('/issues/<id>/completion')
    @login
    def completion(id):
        with store.connect() as c:
            d=store.get_issue(c,id)
            if d['category']!='illegal_dumping' or d['status']=='resolved': raise ValueError('Community completion claims are limited to open cleanup issues. Do not perform electrical or roadway repairs.')
            description=text('description'); evidence=photo(True)
            c.execute('INSERT INTO contributions VALUES(?,?,?,?,?,?,?)',(store.uid(),id,g.user['id'],description,evidence,'pending',store.now()))
            store.history(c,id,g.user['id'],'completion_submitted','Completion awaiting review. No points awarded.')
        flash('Completion awaiting review. An upload does not verify that an issue is fixed.'); return redirect(url_for('issue',id=id))

    @app.get('/admin')
    @admin
    def admin_page():
        with store.connect() as c:
            contributions=c.execute('SELECT x.*,u.name FROM contributions x JOIN users u ON u.id=x.user_id ORDER BY created_at DESC').fetchall()
            reviews=c.execute('SELECT r.*,u.name FROM reviews r JOIN users u ON u.id=r.reviewer ORDER BY created_at DESC').fetchall()
            issues=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM issues')]
            points=c.execute('SELECT value FROM settings WHERE key=?',('approved_contribution',)).fetchone()[0]
        return render_template('admin.html',contributions=contributions,reviews=reviews,issues=issues,points=points)

    @app.post('/admin/review/<id>')
    @admin
    def review(id):
        decision=text('decision',20); reason=text('reason',2000)
        if decision not in {'approved','rejected','revoked'}: raise ValueError('Unknown review decision.')
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE'); x=c.execute('SELECT * FROM contributions WHERE id=?',(id,)).fetchone()
            if not x: abort(404)
            if x['user_id']==g.user['id']: raise ValueError('A different reviewer must review your contribution.')
            if x['status']==decision: flash('This decision is already recorded.'); return redirect(url_for('admin_page'))
            if decision=='revoked' and x['status']!='approved': raise ValueError('Only an approval can be revoked.')
            if x['status']=='approved' and decision!='revoked': raise ValueError('Revoke the approval before changing the decision.')
            rid=store.uid(); c.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?)',(rid,id,g.user['id'],decision,reason,store.now()))
            balance=c.execute('SELECT coalesce(sum(points),0) FROM ledger WHERE contribution_id=?',(id,)).fetchone()[0]
            award=c.execute('SELECT value FROM settings WHERE key=?',('approved_contribution',)).fetchone()[0] if decision=='approved' else 0
            delta=award-balance
            c.execute('INSERT INTO ledger VALUES(?,?,?,?,?,?)',(store.uid(),id,x['user_id'],rid,delta,store.now()))
            c.execute('UPDATE contributions SET status=? WHERE id=?',(decision,id))
            store.history(c,x['issue_id'],g.user['id'],'review_'+decision,reason)
        flash('Review recorded. Points ledger updated. Issue resolution remains a separate explicit action.'); return redirect(url_for('admin_page'))

    @app.post('/admin/points')
    @admin
    def point_rules():
        value=int(text('points',6))
        if not 0<=value<=10000: raise ValueError('Points must be 0–10000.')
        with store.connect() as c: c.execute('UPDATE settings SET value=? WHERE key=?',(value,'approved_contribution'))
        flash('Point rule updated for future approvals. Existing awards are unchanged.'); return redirect(url_for('admin_page'))

    @app.post('/admin/issues/<id>/<action>')
    @admin
    def issue_action(id,action):
        if action=='retry': pipeline.escalate(id)
        elif action=='resolve':
            pipeline.resolve(id)
            with store.connect() as c: store.history(c,id,g.user['id'],'resolution_actor','Resolution action requested by authorized reviewer.')
        else: abort(404)
        flash('Action complete. Messages are generated outputs, not deliveries.'); return redirect(url_for('issue',id=id))

    @app.get('/contributors')
    def contributors():
        with store.connect() as c: rows=c.execute('SELECT u.id,u.name,coalesce(sum(l.points),0) points FROM users u LEFT JOIN ledger l ON u.id=l.user_id GROUP BY u.id ORDER BY points DESC,u.name').fetchall()
        return render_template('contributors.html',users=rows)

    @app.get('/people/<id>')
    def profile(id):
        with store.connect() as c:
            person=c.execute('SELECT id,name,created_at FROM users WHERE id=?',(id,)).fetchone()
            if not person: abort(404)
            contributions=c.execute('SELECT * FROM contributions WHERE user_id=? ORDER BY created_at DESC',(id,)).fetchall()
            ledger=c.execute('SELECT * FROM ledger WHERE user_id=? ORDER BY created_at DESC',(id,)).fetchall()
        return render_template('profile.html',person=person,contributions=contributions,ledger=ledger,points=sum(l['points'] for l in ledger))

    @app.get('/me')
    @login
    def me():
        with store.connect() as c:
            notices=c.execute('SELECT * FROM notices WHERE user_id=? ORDER BY created_at DESC',(g.user['id'],)).fetchall()
            activities=c.execute('SELECT a.* FROM activities a JOIN participants p ON a.id=p.activity_id WHERE p.user_id=?',(g.user['id'],)).fetchall()
        return render_template('me.html',notices=notices,activities=activities)

    @app.get('/photos/<name>')
    @login
    def photos(name):
        if '/' in name or not name.endswith('.jpg'): abort(404)
        return send_from_directory(app.config['UPLOAD_FOLDER'],name,mimetype='image/jpeg')

    @app.get('/sf311')
    def sf311():
        stats=None
        if request.args.get('lat'):
            lat,lon=store.coordinates(request.args.get('lat'),request.args.get('lon'))
            latest=es_store.request('POST','/sf311/_search',{'size':0,'aggs':{'latest':{'max':{'field':'requested_datetime'}}}})['aggregations']['latest']['value']
            if latest is not None:
                stats=es_store.request('POST','/sf311/_search',{'size':10,'query':{'bool':{'filter':[{'geo_distance':{'distance':'500m','location':{'lat':lat,'lon':lon}}},{'range':{'requested_datetime':{'gte':latest-30*86400000,'lte':latest,'format':'epoch_millis'}}}]}},'aggs':{'categories':{'terms':{'field':'service_name','size':5}}},'track_total_hits':True,'_source':['service_name','status_description','address','requested_datetime']})
        return render_template('sf311.html',stats=stats)

    @app.get('/healthz')
    def health():
        with store.connect() as c: c.execute('SELECT 1')
        return {'status':'ok','search_backend':es_store.backend(),'mistral_configured':bool(os.environ.get('MISTRAL_API_KEY'))}

    @app.cli.command('make-admin')
    def make_admin():
        import click
        email=click.prompt('Existing account email')
        with store.connect() as c:
            result=c.execute("UPDATE users SET role='admin' WHERE email=?",(email.lower(),))
            if not result.rowcount: raise click.ClickException('Account not found. Register first.')
        click.echo('Admin role granted. Sign in again.')
    @app.cli.command('sync-search')
    def sync_search():
        with store.connect() as c: es_store.sync(c)
        print('Search projection synchronized.')
    return app

if __name__=='__main__': create_app().run(port=int(os.environ.get('PORT','8001')))
