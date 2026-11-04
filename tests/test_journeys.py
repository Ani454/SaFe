"""Real persistent application journeys; Mistral/Elasticsearch are mocked explicitly."""
import io,json,os,tempfile,unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from PIL import Image
import store,pipeline,es_store,mistral_ai as ai
from website import create_app

class Journeys(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.env=patch.dict(os.environ,{'SAFE_DB':self.tmp.name+'/safe.db','SAFE_STORAGE':self.tmp.name,'SAFE_SEARCH_BACKEND':'sqlite'})
  self.env.start(); self.app=create_app({'TESTING':True,'UPLOAD_FOLDER':self.tmp.name+'/uploads'}); self.client=self.app.test_client()
  self.users=[]
  with store.connect() as c:
   for n in range(12):
    id=store.uid(); self.users.append(id); c.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',(id,'person'+str(n)+'@example.test','Neighbor '+str(n),'unused','admin' if n==11 else 'resident',store.now()))
  self.cls=patch.object(ai,'classify_report',return_value={'category':'illegal_dumping','summary':'Mattress at 16th and Mission','severity':3});self.cls.start()
  self.same=patch.object(ai,'is_same_issue',return_value=True);self.same.start()
  self.draft=patch.object(ai,'draft_authority_email',return_value='Subject: 10 reports — draft only');self.draft_mock=self.draft.start()
  self.notice=patch.object(ai,'draft_resolution_notice',return_value='This issue is recorded as resolved.');self.notice_mock=self.notice.start()
 def tearDown(self):
  for p in [self.cls,self.same,self.draft,self.notice,self.env]:p.stop()
  self.tmp.cleanup()
 def sign(self,n):
  with self.client.session_transaction() as s:s['user_id']=self.users[n];s['csrf']='test-csrf'
 def post(self,url,**data):return self.client.post(url,data={'csrf':'test-csrf',**data},follow_redirects=False)
 def report(self,n=0,key=None):return pipeline.submit(self.users[n],'A mattress blocks the sidewalk',37.7652,-122.4195,key)
 def picture(self):
  b=io.BytesIO();Image.new('RGB',(10,10),'green').save(b,'PNG');b.seek(0);return b,'after.png'
 def contribution(self,id):
  self.sign(0);r=self.post('/issues/'+id+'/completion',description='Removed ordinary litter around the mattress',photo=self.picture());self.assertEqual(r.status_code,302)
  with store.connect() as c:return c.execute('SELECT id FROM contributions').fetchone()[0]
 def test_tenth_eleventh_resolution_and_retry(self):
  id=None
  for n in range(10):id=self.report(n)['issue_id']
  d=es_store.get_issue(id);self.assertEqual(d['report_count'],10);self.assertEqual(d['status'],'escalated');self.draft_mock.assert_called_once()
  self.report(10);self.assertEqual(es_store.get_issue(id)['report_count'],10);self.draft_mock.assert_called_once()
  self.assertEqual(len(pipeline.resolve(id)),10);self.assertEqual(pipeline.resolve(id),[]);self.notice_mock.assert_called_once()
  with store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM notices').fetchone()[0],10)
 def test_retry_draft_failure_retains_report(self):
  for n in range(9):id=self.report(n)['issue_id']
  with patch.object(ai,'draft_authority_email',side_effect=ai.MistralError('offline')):self.report(9)
  self.assertEqual(es_store.get_issue(id)['report_count'],10);self.assertEqual(es_store.get_issue(id)['status'],'open')
  pipeline.escalate(id);pipeline.escalate(id);self.assertEqual(es_store.get_issue(id)['status'],'escalated');self.draft_mock.assert_called_once()
 def test_different_object_and_match_failure(self):
  first=self.report()['issue_id']
  with patch.object(ai,'is_same_issue',return_value=False):second=self.report(1)['issue_id']
  self.assertNotEqual(first,second)
  with patch.object(ai,'is_same_issue',side_effect=ai.MistralError('offline')):
   with self.assertRaises(ai.MistralError):self.report(2)
  self.assertEqual(es_store.get_issue(first)['report_count'],1)
 def test_old_outside_radius_resolved_excluded(self):
  id=self.report()['issue_id']
  with store.connect() as c:
   self.assertIsNone(es_store.match(c,'graffiti',37.7652,-122.4195));self.assertIsNone(es_store.match(c,'illegal_dumping',37.8,-122.4))
   d=store.get_issue(c,id);d['created_at']=(datetime.now(timezone.utc)-timedelta(days=15)).isoformat();store.save(c,d)
  self.assertIsNone(es_store.find_matching_issue('illegal_dumping',37.7652,-122.4195))
 def test_request_idempotency(self):
  a=self.report(key='request-1');b=self.report(key='request-1');self.assertEqual(a['issue_id'],b['issue_id']);self.assertEqual(es_store.get_issue(a['issue_id'])['report_count'],1)
 def test_missing_invalid_coordinates(self):
  for lat,lon in [(None,0),('',0),(91,0),(0,float('nan'))]:
   with self.assertRaises(ValueError):pipeline.submit(self.users[0],'report',lat,lon)
 def test_review_award_repeat_reverse_and_permissions(self):
  id=self.report()['issue_id'];cid=self.contribution(id)
  self.assertEqual(self.post('/admin/review/'+cid,decision='approved',reason='Checked evidence').status_code,403)
  self.sign(11)
  for _ in range(2):self.assertEqual(self.post('/admin/review/'+cid,decision='approved',reason='Checked evidence').status_code,302)
  with store.connect() as c:
   self.assertEqual(c.execute('SELECT sum(points) FROM ledger').fetchone()[0],50);self.assertEqual(c.execute('SELECT count(*) FROM ledger').fetchone()[0],1)
  self.assertEqual(es_store.get_issue(id)['status'],'open')
  self.post('/admin/review/'+cid,decision='revoked',reason='Evidence belongs to a different issue')
  with store.connect() as c:self.assertEqual(c.execute('SELECT sum(points) FROM ledger').fetchone()[0],0);self.assertEqual(c.execute('SELECT count(*) FROM reviews').fetchone()[0],2)
 def test_reject_and_self_review(self):
  id=self.report()['issue_id'];cid=self.contribution(id);self.sign(11)
  self.post('/admin/review/'+cid,decision='rejected',reason='Photo does not match')
  with store.connect() as c:
   self.assertEqual(c.execute('SELECT sum(points) FROM ledger').fetchone()[0],0)
   c.execute("UPDATE users SET role='admin' WHERE id=?",(self.users[0],))
  self.sign(0);self.assertEqual(self.post('/admin/review/'+cid,decision='approved',reason='My own upload').status_code,400)
 def test_activity_capacity_leave_and_professional_restrictions(self):
  id=self.report()['issue_id'];self.sign(0)
  r=self.post('/activities',issue_id=id,title='Saturday cleanup',description='Ordinary litter only; no hazardous material',starts_at='2099-11-07T10:00:00-08:00',meeting='16th and Mission',capacity='1');self.assertEqual(r.status_code,302);url=r.location
  self.assertEqual(self.post(url,action='join').status_code,302);self.sign(1);self.assertEqual(self.post(url,action='join').status_code,400)
  self.sign(0);self.post(url,action='leave');self.sign(1);self.assertEqual(self.post(url,action='join').status_code,302)
  with store.connect() as c:d=store.get_issue(c,id);d['category']='streetlight';store.save(c,d)
  self.assertEqual(self.post('/activities',issue_id=id,title='Repair',description='test',starts_at='2099-11-07T10:00:00-08:00',meeting='test',capacity='3').status_code,400)
 def test_photo_required_and_no_automatic_reward(self):
  id=self.report()['issue_id'];self.sign(0)
  self.assertEqual(self.post('/issues/'+id+'/completion',description='Claim without photo').status_code,400)
  self.contribution(id)
  with store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM ledger').fetchone()[0],0)
 def test_notices_failure_rolls_back_resolution(self):
  id=self.report()['issue_id']
  with patch.object(ai,'draft_resolution_notice',side_effect=ai.MistralError('offline')):
   with self.assertRaises(ai.MistralError):pipeline.resolve(id)
  self.assertEqual(es_store.get_issue(id)['status'],'open');self.assertEqual(len(pipeline.resolve(id)),1)
 def test_pages_and_persistence(self):
  id=self.report()['issue_id'];self.sign(11)
  for path in ['/','/report','/issues/'+id,'/activities','/contributors','/people/'+self.users[0],'/me','/admin','/sf311','/healthz']:
   with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)
  second=create_app({'TESTING':True});self.assertIn(b'Mattress',second.test_client().get('/').data)
 def test_csrf_and_registration_login(self):
  self.assertEqual(self.client.post('/auth/register',data={}).status_code,400)
  self.client.get('/auth/register')
  with self.client.session_transaction() as s:csrf=s['csrf']
  r=self.client.post('/auth/register',data={'csrf':csrf,'name':'New neighbor','email':'new@example.test','password':'a-long-password-123'});self.assertEqual(r.status_code,302)
  with self.client.session_transaction() as s:csrf=s['csrf']
  self.client.post('/logout',data={'csrf':csrf});self.client.get('/auth/login')
  with self.client.session_transaction() as s:csrf=s['csrf']
  self.assertEqual(self.client.post('/auth/login',data={'csrf':csrf,'email':'new@example.test','password':'a-long-password-123'}).status_code,302)
 def test_report_provider_failure_preserves_input(self):
  self.sign(0)
  with patch.object(ai,'classify_report',side_effect=ai.MistralError('Provider unavailable')):
   r=self.post('/report',description='A mattress near Mission',lat='37.77',lon='-122.42',request_key='retry-key')
   self.assertEqual(r.status_code,503);self.assertIn(b'A mattress near Mission',r.data);self.assertIn(b'retry-key',r.data)
 def test_concurrent_reports_and_identical_retries(self):
  from concurrent.futures import ThreadPoolExecutor
  with ThreadPoolExecutor(max_workers=6) as pool:
   results=list(pool.map(lambda n:self.report(n,key='parallel-'+str(n)),range(10)))
  self.assertEqual(len(set(r['issue_id'] for r in results)),1)
  self.assertEqual(es_store.get_issue(results[0]['issue_id'])['report_count'],10)
  self.draft_mock.assert_called_once()
 def test_create_issue_contract_is_distinct_and_filters(self):
  first=es_store.create_issue('illegal_dumping','Mattress',37.77,-122.42,self.users[0],'Mattress')
  second=es_store.create_issue('graffiti','Wall',37.77,-122.42,self.users[0],'Wall')
  self.assertNotEqual(first,second)
  self.assertIn(b'Mattress',self.client.get('/?category=illegal_dumping').data)
  self.assertNotIn(b'>Wall<',self.client.get('/?category=illegal_dumping').data)
  self.assertEqual(self.client.get('/?distance=50').status_code,400)
 def test_production_requires_secret(self):
  with patch.dict(os.environ,{'SAFE_ENV':'production','SAFE_SECRET_KEY':''}):
   with self.assertRaises(RuntimeError):create_app()
 def test_real_elasticsearch_query_shape(self):
  with patch.dict(os.environ,{'SAFE_SEARCH_BACKEND':'elasticsearch'}),patch.object(es_store,'sync'),patch.object(es_store,'request',return_value={'hits':{'hits':[]}}) as req:
   self.assertIsNone(es_store.find_matching_issue('graffiti',37.77,-122.42));query=req.call_args.args[2];self.assertEqual(query['size'],1);self.assertEqual(query['query']['bool']['filter'][1]['geo_distance']['distance'],'50m');self.assertIn('_geo_distance',query['sort'][0])

if __name__=='__main__':unittest.main()
