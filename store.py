"""Transactional application records; SQLite is the source of truth."""
import json, math, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return uuid.uuid4().hex
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'resident',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS issues(id TEXT PRIMARY KEY,doc TEXT NOT NULL,dirty INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES issues(id),user_id TEXT NOT NULL REFERENCES users(id),text TEXT NOT NULL,created_at TEXT NOT NULL,request_key TEXT UNIQUE NOT NULL,photo TEXT);
CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES issues(id),actor TEXT,kind TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notices(issue_id TEXT NOT NULL REFERENCES issues(id),user_id TEXT NOT NULL REFERENCES users(id),text TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(issue_id,user_id));
CREATE TABLE IF NOT EXISTS activities(id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES issues(id),organizer TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,description TEXT NOT NULL,starts_at TEXT NOT NULL,meeting TEXT NOT NULL,capacity INTEGER NOT NULL CHECK(capacity>0),created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS participants(activity_id TEXT NOT NULL REFERENCES activities(id),user_id TEXT NOT NULL REFERENCES users(id),PRIMARY KEY(activity_id,user_id));
CREATE TABLE IF NOT EXISTS contributions(id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES issues(id),user_id TEXT NOT NULL REFERENCES users(id),description TEXT NOT NULL,photo TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,contribution_id TEXT NOT NULL REFERENCES contributions(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY,contribution_id TEXT NOT NULL REFERENCES contributions(id),user_id TEXT NOT NULL REFERENCES users(id),review_id TEXT UNIQUE NOT NULL REFERENCES reviews(id),points INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value INTEGER NOT NULL);
INSERT OR IGNORE INTO settings VALUES('approved_contribution',50);
'''
class Connection(sqlite3.Connection):
    def __exit__(self,*args):
        try: return super().__exit__(*args)
        finally: self.close()

def connect():
    path=os.environ.get('SAFE_DB','instance/safe.db'); Path(path).parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(path,timeout=150,factory=Connection); c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL'); return c

def init():
    with connect() as c: c.executescript(SCHEMA)

def get_issue(c,id):
    row=c.execute('SELECT doc FROM issues WHERE id=?',(id,)).fetchone()
    if not row: raise ValueError('Issue not found.')
    return json.loads(row['doc'])

def save(c,doc):
    c.execute('INSERT INTO issues(id,doc,dirty) VALUES(?,?,1) ON CONFLICT(id) DO UPDATE SET doc=excluded.doc,dirty=1',(doc['issue_id'],json.dumps(doc)))

def history(c,id,actor,kind,detail):
    c.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(uid(),id,actor,kind,detail,now()))

def coordinates(lat,lon):
    try:
        if isinstance(lat,bool) or isinstance(lon,bool) or lat is None or lon is None or str(lat).strip()=='' or str(lon).strip()=='': raise ValueError
        lat,lon=float(lat),float(lon)
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180: raise ValueError
    except (TypeError,ValueError): raise ValueError('Select a valid location with latitude and longitude.')
    return lat,lon

def distance(a,b):
    r=math.pi/180; p,q=a['lat']*r,b['lat']*r
    v=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin((b['lon']-a['lon'])*r/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(v)))
