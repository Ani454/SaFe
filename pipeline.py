"""Serialized, retryable reporting lifecycle. All messages are generated drafts."""
import json
import store,es_store,mistral_ai as ai
THRESHOLD=10

def attach(c,d,reporter,text,key,photo):
    c.execute('INSERT INTO reports VALUES(?,?,?,?,?,?,?)',(store.uid(),d['issue_id'],reporter,text,store.now(),key,photo))
    d['report_count']+=1; d['updated_at']=store.now()
    if reporter not in d['reporters']: d['reporters'].append(reporter)
    d['report_texts'].append(text); store.save(c,d)
    store.history(c,d['issue_id'],reporter,'report_added','A report was attached to this issue.')

def draft(c,d):
    if d['status']=='escalated' or d['report_count']<THRESHOLD: return
    d['agency_draft']=ai.draft_authority_email(d,es_store.agency_for(d['category']))
    d['status']='escalated'; d['draft_error']=None; store.save(c,d)
    store.history(c,d['issue_id'],None,'draft_created','Consolidated agency draft generated. Nothing sent.')

def submit(reporter,text,lat,lon,key=None,photo=None,classification=None):
    lat,lon=store.coordinates(lat,lon); text=ai._text(text,'Description'); key=key or store.uid()
    with store.connect() as c:
        existing=c.execute('SELECT issue_id FROM reports WHERE request_key=? AND user_id=?',(key,reporter)).fetchone()
        if existing: return {'issue_id':existing['issue_id'],'message':'Your report is already recorded.'}
    classified=classification or ai.classify_report(text)
    # BEGIN IMMEDIATE serializes candidate selection, attachment and generation across workers.
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT issue_id FROM reports WHERE request_key=? AND user_id=?',(key,reporter)).fetchone()
        if existing: return {'issue_id':existing['issue_id'],'message':'Your report is already recorded.'}
        d=es_store.match(c,classified['category'],lat,lon)
        if d and not ai.is_same_issue(text,d['summary']): d=None
        if d and d['status']=='escalated': return {'issue_id':d['issue_id'],'message':'This issue already has an escalation draft. No additional report or draft was added.'}
        if not d:
            d={'issue_id':store.uid(),'category':classified['category'],'summary':classified['summary'],'severity':classified['severity'],'location':{'lat':lat,'lon':lon},'created_at':store.now(),'updated_at':store.now(),'status':'open','report_count':0,'reporters':[],'report_texts':[]}
            store.save(c,d)
        attach(c,d,reporter,text,key,photo)
        try: draft(c,d)
        except ai.MistralError:
            d['draft_error']='Draft generation failed. Your report was saved; an administrator can retry.'; store.save(c,d)
        return {'issue_id':d['issue_id'],'message':d.get('draft_error') or ('Agency draft ready for review. Nothing sent.' if d['status']=='escalated' else 'Your report counts. Thank you for helping your neighborhood.')}

def submit_report(reporter,text,lat,lon): return submit(reporter,text,lat,lon)['message']
def escalate(issue_id):
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE'); d=store.get_issue(c,issue_id); draft(c,d)

def resolve(issue_id):
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE'); d=store.get_issue(c,issue_id)
        if d['status']=='resolved': return []
        d['status']='resolved'; d['resolution']='An authorized reviewer explicitly marked this issue resolved.'
        notice=ai.draft_resolution_notice(d)  # Failure rolls back; retry produces one batch.
        for user in d['reporters']: c.execute('INSERT INTO notices VALUES(?,?,?,?)',(issue_id,user,notice,store.now()))
        store.save(c,d); store.history(c,issue_id,None,'resolved','Explicitly resolved; resident notices generated, not delivered.')
        return [notice for _ in d['reporters']]
