from fastapi.testclient import TestClient
from app.main import create_app

CSV='id,symbol,side,quantity,price,fee,currency,traded_at\nt1,DEMO,buy,100,10,1,CNY,2024-01-02T10:00:00+08:00\n'
def client(tmp_path): return TestClient(create_app(str(tmp_path/'test.db')))

def test_complete_chain_and_isolation(tmp_path):
    a=client(tmp_path)
    c=a.post('/api/demo').json(); id=c['id']
    assert len(c['trades'])==3
    timeline=a.get(f'/api/cases/{id}/timeline',params={'cutoff':'2024-03-04T10:15:00+08:00'}).json()
    assert 'E3' not in {e['id'] for e in timeline['visible']}
    assert timeline['hidden_count']>0
    r=a.post(f'/api/cases/{id}/reviews',json={'cutoff':'2024-03-04T10:15:00+08:00','trade_ids':['D1'],'mode':'rules'})
    assert r.status_code==200,r.text
    review=r.json(); item=review['improvements'][0]
    resp=a.post(f'/api/cases/{id}/checklist',json={'text':item['text'],'review_id':review['id'],'evidence_ids':item['evidence_ids']})
    assert resp.status_code==200
    entry=resp.json()
    assert a.patch(f'/api/cases/{id}/checklist/{entry["id"]}',json={'done':True}).json()['done'] is True
    assert a.get(f'/api/cases/{id}/export').status_code==200
    b=TestClient(a.app)
    assert b.get(f'/api/cases/{id}').status_code==404
    cookies=dict(a.cookies)
    restarted=TestClient(create_app(str(tmp_path/'test.db')))
    restarted.cookies.update(cookies)
    assert restarted.get(f'/api/cases/{id}').json()['checklist'][0]['done'] is True

def test_import_preview_and_atomic_errors(tmp_path):
    a=client(tmp_path); c=a.post('/api/cases',json={'title':'新案例'}).json(); url=f'/api/cases/{c["id"]}/imports'
    assert len(a.post(url,json={'csv':CSV}).json()['valid_rows'])==1
    assert not a.get(f'/api/cases/{c["id"]}').json()['trades']
    assert a.post(url,json={'csv':CSV,'confirm':True}).status_code==200
    assert a.post(url,json={'csv':CSV,'confirm':True}).status_code==422
    assert a.post(url,json={'csv':CSV+'bad,row\n','confirm':True}).status_code==422
    assert len(a.get(f'/api/cases/{c["id"]}').json()['trades'])==1

def test_reason_recorded_at_server_and_oversize(tmp_path):
    a=client(tmp_path); c=a.post('/api/demo').json(); id=c['id']
    r=a.put(f'/api/cases/{id}/reasons/D1',json={'text':'事后回忆','formed_at':'2024-03-04T09:00:00+08:00'})
    assert r.status_code==200 and r.json()['backfilled']
    assert a.post('/api/cases',json={'title':'a'*101}).status_code==422
    assert a.post('/api/cases',content='x'*1100000,headers={'Content-Type':'application/json'}).status_code==413

def test_health_and_injection(tmp_path,monkeypatch):
    monkeypatch.delenv('AI_API_KEY',raising=False)
    a=client(tmp_path)
    assert a.get('/api/health').json()['ai_configured'] is False
    assert a.post('/api/cases',json={'title':'<script>alert(1)</script>'}).status_code==200
    assert a.get('/api/providers').json()[0]['status']=='unavailable'

def test_unknown_time_validation(tmp_path):
    a=client(tmp_path); c=a.post('/api/demo').json()
    assert a.get(f'/api/cases/{c["id"]}/timeline',params={'cutoff':'2024-01-01T10:00:00'}).status_code==422

def test_learning_reused_across_own_cases_only(tmp_path):
    a=client(tmp_path); case=a.post('/api/demo').json(); id=case['id']
    r=a.post(f'/api/cases/{id}/reviews',json={'cutoff':'2024-03-04T10:15:00+08:00','trade_ids':['D1'],'mode':'rules'}).json()
    item=r['improvements'][0]
    a.post(f'/api/cases/{id}/checklist',json={'text':item['text'],'review_id':r['id'],'evidence_ids':item['evidence_ids']})
    assert a.get('/api/learning').json()[0]['case_id']==id
    assert TestClient(a.app).get('/api/learning').json()==[]

def test_provider_failure_is_visible(tmp_path,monkeypatch):
    monkeypatch.delenv('FUYAO_API_KEY',raising=False)
    a=client(tmp_path); c=a.post('/api/demo').json()
    r=a.post(f'/api/cases/{c["id"]}/providers/fuyao',json={'symbol':'600000.SH','start':'2024-03-01T00:00:00+08:00','end':'2024-03-08T00:00:00+08:00'})
    assert r.status_code==422
    c2=a.get(f'/api/cases/{c["id"]}').json()
    assert c2['provider_last_call']['status']=='failed'
    assert c2['evidence']==c['evidence']

def test_source_snapshot_is_opt_in_and_paths_are_allowlisted(tmp_path,monkeypatch):
    monkeypatch.delenv('PUBLIC_SOURCE_PATH',raising=False)
    a=client(tmp_path)
    assert a.get('/source.git/HEAD').status_code==404
    root=tmp_path/'source.git'; root.mkdir(); (root/'HEAD').write_text('ref: refs/heads/feat/zhixing\n'); (root/'config').write_text('must not expose')
    (root/'info').mkdir(); (root/'info'/'refs').write_text('test')
    monkeypatch.setenv('PUBLIC_SOURCE_PATH',str(root))
    b=TestClient(create_app(':memory:'))
    assert b.get('/source.git/HEAD').status_code==200
    assert b.get('/source.git/config').status_code==404
    assert b.get('/source.git/objects/../../config').status_code==404

def test_explicit_public_origin_behind_tls_proxy(tmp_path,monkeypatch):
    monkeypatch.setenv('PUBLIC_ORIGIN','https://example.test')
    a=client(tmp_path)
    assert a.post('/api/demo',json={},headers={'Origin':'https://example.test'}).status_code==200
    assert a.post('/api/demo',json={},headers={'Origin':'https://evil.test'}).status_code==403

def test_render_external_url_is_canonical_origin(tmp_path,monkeypatch):
    monkeypatch.delenv('PUBLIC_ORIGIN',raising=False)
    monkeypatch.setenv('RENDER_EXTERNAL_URL','https://zhixing-example.onrender.com')
    a=client(tmp_path)
    assert a.post('/api/demo',json={},headers={'Origin':'https://zhixing-example.onrender.com'}).status_code==200
    assert a.post('/api/demo',json={},headers={'Origin':'https://evil.test'}).status_code==403
