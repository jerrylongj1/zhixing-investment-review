from datetime import datetime
import pytest
from app.reviews import build_review, validate_review, ReviewError
from app.demo import populate_demo
from app.models import ReviewContent

CUTOFF=datetime.fromisoformat('2024-03-04T10:15:00+08:00')
def demo(): return populate_demo(dict(id='c',title='测试',trades=[],reasons={},evidence=[]))
def test_rules_only_uses_known_evidence():
    c=demo(); r=build_review(c,['D1'],CUTOFF,'rules')
    assert r['mode']=='rules'
    allowed={e['id'] for e in r['evidence_snapshot']}
    assert 'E1' in allowed and 'E3' not in allowed and 'E6' not in allowed
    assert all(set(i['evidence_ids'])<=allowed for k in ['facts','hypotheses','bias_signals','uncertainties','improvements'] for i in r[k])
    assert 'E4' not in str(r['evidence_snapshot'])

def test_ai_missing_config(monkeypatch):
    monkeypatch.delenv('AI_API_KEY',raising=False)
    with pytest.raises(ReviewError,match='未配置'): build_review(demo(),['D1'],CUTOFF,'ai')

def test_forged_reference_and_advice():
    r=build_review(demo(),['D1'],CUTOFF,'rules')
    r['facts'][0]['evidence_ids']=['OTHER_CASE']
    with pytest.raises(ReviewError): validate_review(r,{'E1'},{'D1'})
    r=build_review(demo(),['D1'],CUTOFF,'rules')
    r['facts'][0]['text']='建议买入该股票，保证收益'
    with pytest.raises(ReviewError): validate_review(r,{e['id'] for e in r['evidence_snapshot']},{'D1'})

def test_unavailable_selected_trade():
    with pytest.raises(ReviewError): build_review(demo(),['D3'],CUTOFF,'rules')

def test_backfill_not_known():
    r=build_review(demo(),['D2'],datetime.fromisoformat('2024-03-06T14:20:00+08:00'),'rules')
    assert 'R-D2' not in {e['id'] for e in r['evidence_snapshot']}
    assert any('补录' in i['text'] for i in r['uncertainties'])

def test_batch_cannot_use_later_information_for_earlier_decision():
    c=demo(); r=build_review(c,['D1','D2'],datetime.fromisoformat('2024-03-12T16:00:00+08:00'),'rules')
    assert 'E3' not in r['knowledge_by_decision']['D1']
    assert 'E3' in r['knowledge_by_decision']['D2']
    assert 'E4' not in {e['id'] for e in r['evidence_snapshot']}
    bad={s:r[s] for s in ['facts','hypotheses','bias_signals','uncertainties','improvements']}
    bad['facts'][0]={'text':'较早决策使用稍后收盘值','evidence_ids':['E3'],'decision_ids':['D1']}
    with pytest.raises(ReviewError):
        validate_review(bad,{e['id'] for e in r['evidence_snapshot']},{'D1','D2'},r['knowledge_by_decision'])

def test_ai_timeout_invalid_json_and_future_filter(monkeypatch):
    import httpx
    import app.reviews as reviews
    monkeypatch.setenv('AI_API_KEY','test-not-secret'); monkeypatch.setenv('AI_MODEL','test-model')
    real_client=httpx.Client
    seen=[]
    def handle(req):
        import json
        payload=json.loads(req.content); ctx=json.loads(payload['messages'][1]['content']); seen.append(ctx)
        assert 'E4' not in {e['id'] for e in ctx['evidence']}
        raise httpx.ReadTimeout('simulated',request=req)
    monkeypatch.setattr(reviews.httpx,'Client',lambda **kw:real_client(transport=httpx.MockTransport(handle)))
    with pytest.raises(ReviewError,match='超时'): build_review(demo(),['D1'],CUTOFF,'ai')
    assert seen
    monkeypatch.setattr(reviews.httpx,'Client',lambda **kw:real_client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'not json'}}]}))))
    with pytest.raises(ReviewError,match='无效 JSON'): build_review(demo(),['D1'],CUTOFF,'ai')

@pytest.mark.parametrize('text',['请买入 DEMO.A 并持有，下周会上涨。','现在清仓，未来一定会跌。','Buy DEMO.A now and hold it.','价格明天将突破前高'])
def test_imperative_or_prediction_rejected(text):
    r=build_review(demo(),['D1'],CUTOFF,'rules'); r['improvements'][0]['text']=text
    with pytest.raises(ReviewError): validate_review(r,{e['id'] for e in r['evidence_snapshot']},{'D1'})

@pytest.mark.parametrize('envelope',[
    {'choices':[]},
    {'choices':[{'finish_reason':'stop','message':{'content':'[]'}}]},
    [],
])
def test_malformed_model_container_is_controlled(monkeypatch,envelope):
    import httpx
    import app.reviews as reviews
    monkeypatch.setenv('AI_API_KEY','test-not-secret');monkeypatch.setenv('AI_MODEL','test-model')
    real_client=httpx.Client
    monkeypatch.setattr(reviews.httpx,'Client',lambda **kw:real_client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=envelope))))
    with pytest.raises(ReviewError): build_review(demo(),['D1'],CUTOFF,'ai')

def test_full_supported_batch_capacity():
    c=demo(); c['trades']=[dict(c['trades'][0],id=f'B{i}') for i in range(100)]; c['reasons']={}
    r=build_review(c,[t['id'] for t in c['trades']],CUTOFF,'rules')
    assert len(r['facts'])==100
    assert len(r['uncertainties'])>=101

@pytest.mark.parametrize('trade_id',['buy-1','sell-1','买入记录1'])
def test_legitimate_trade_ids_do_not_trigger_advice_filter(trade_id):
    c=demo();c['trades']=[dict(c['trades'][0],id=trade_id)];c['reasons']={}
    r=build_review(c,[trade_id],CUTOFF,'rules')
    assert r['trade_ids']==[trade_id]
    assert r['uncertainties'][1]['decision_ids']==[trade_id]
