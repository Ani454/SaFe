"""Elasticsearch issue projection and preserved public storage contracts."""
import json, os
from datetime import datetime, timedelta, timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import store

AGENCIES={'illegal_dumping':'San Francisco Public Works','graffiti':'San Francisco Public Works','streetlight':'Responsible streetlight operator — review required','pothole':'San Francisco Public Works','other':'Agency routing review required'}
def agency_for(category): return AGENCIES.get(category,'Agency routing review required')
def backend(): return os.environ.get('SAFE_SEARCH_BACKEND','elasticsearch')
def request(method,path,data=None):
    url=os.environ.get('ES_URL','').rstrip('/')
    if not url: raise RuntimeError('Configure ES_URL for Elasticsearch, or explicitly select SAFE_SEARCH_BACKEND=sqlite for local development.')
    headers={'Content-Type':'application/json'}
    if os.environ.get('ES_API_KEY'): headers['Authorization']='ApiKey '+os.environ['ES_API_KEY']
    try:
        with urlopen(Request(url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method),timeout=15) as r: return json.load(r)
    except (HTTPError,URLError,OSError,ValueError) as e: raise RuntimeError('Elasticsearch is unavailable. No matching decision was made; please retry.') from e

def sync(c):
    if backend()=='sqlite': return
    mapping={'properties':{'category':{'type':'keyword'},'location':{'type':'geo_point'},'status':{'type':'keyword'},'created_at':{'type':'date'},'summary':{'type':'text'}}}
    # Idempotent index existence check; never touches sf311.
    try: request('GET','/safe_issues/_mapping')
    except RuntimeError:
        request('PUT','/safe_issues',{'mappings':mapping})
    for row in c.execute('SELECT * FROM issues WHERE dirty=1').fetchall():
        doc=json.loads(row['doc'])
        projection={k:doc[k] for k in ['issue_id','category','summary','location','status','created_at','updated_at','report_count']}
        request('PUT','/safe_issues/_doc/'+row['id']+'?refresh=wait_for',projection)
        c.execute('UPDATE issues SET dirty=0 WHERE id=?',(row['id'],))

def match(c,category,lat,lon):
    cutoff=(datetime.now(timezone.utc)-timedelta(days=14)).isoformat()
    if backend()=='sqlite':
        docs=[json.loads(r['doc']) for r in c.execute('SELECT doc FROM issues')]
        docs=[d for d in docs if d['category']==category and d['status']!='resolved' and d['created_at']>=cutoff and store.distance(d['location'],{'lat':lat,'lon':lon})<=50]
        return min(docs,key=lambda d:store.distance(d['location'],{'lat':lat,'lon':lon})) if docs else None
    sync(c)
    query={'size':1,'query':{'bool':{'filter':[{'term':{'category':category}},{'geo_distance':{'distance':'50m','location':{'lat':lat,'lon':lon}}},{'range':{'created_at':{'gte':cutoff}}}],'must_not':[{'term':{'status':'resolved'}}]}},'sort':[{'_geo_distance':{'location':{'lat':lat,'lon':lon},'order':'asc','unit':'m'}}]}
    hits=request('POST','/safe_issues/_search',query)['hits']['hits']
    if not hits: return None
    # Always hydrate from authoritative transactional state, never mutate a stale hit.
    try: return store.get_issue(c,hits[0]['_id'])
    except ValueError: raise RuntimeError('Search index needs reconciliation before reporting can continue.')

def find_matching_issue(category,lat,lon):
    lat,lon=store.coordinates(lat,lon)
    with store.connect() as c: return match(c,category,lat,lon)
def get_issue(issue_id):
    with store.connect() as c: return store.get_issue(c,issue_id)
def create_issue(category,summary,lat,lon,reporter,text):
    lat,lon=store.coordinates(lat,lon)
    if category not in AGENCIES: raise ValueError('Unknown category.')
    doc={'issue_id':store.uid(),'category':category,'summary':summary,'severity':2,'location':{'lat':lat,'lon':lon},'created_at':store.now(),'updated_at':store.now(),'status':'open','report_count':0,'reporters':[],'report_texts':[]}
    from pipeline import attach
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE'); store.save(c,doc); attach(c,doc,reporter,text,store.uid(),None)
    return doc['issue_id']
def add_report(issue_id,reporter,text):
    from pipeline import attach
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE'); d=store.get_issue(c,issue_id)
        if d['status']!='open': return d['report_count']
        attach(c,d,reporter,text,store.uid(),None); return d['report_count']
def mark_escalated(issue_id):
    from pipeline import escalate
    escalate(issue_id); return get_issue(issue_id)
def mark_resolved(issue_id):
    from pipeline import resolve
    resolve(issue_id); return get_issue(issue_id)
