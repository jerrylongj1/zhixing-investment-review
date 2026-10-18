from datetime import datetime
import httpx
import pytest
from app.providers import fetch_fuyao, ProviderError
START=datetime.fromisoformat('2024-03-01T00:00:00+08:00')
END=datetime.fromisoformat('2024-03-08T00:00:00+08:00')

def test_missing_provider_key(monkeypatch):
    monkeypatch.delenv('FUYAO_API_KEY',raising=False)
    with pytest.raises(ProviderError,match='未配置'): fetch_fuyao('600000.SH',START,END)

def test_provider_success_preserves_unknown_publication(monkeypatch):
    monkeypatch.setenv('FUYAO_API_KEY','test-not-secret')
    def handle(req):
        assert req.headers['X-api-key']=='test-not-secret'
        assert req.url.params['adjust']=='none'
        return httpx.Response(200,json={'code':0,'request_id':'test-request','data':{'timestamp':1709251200000,'item':[{'date_ms':1709251200000,'open_price':10,'close_price':11,'volume':100}]}})
    with httpx.Client(transport=httpx.MockTransport(handle)) as c:
        r=fetch_fuyao('600000.SH',START,END,c)
    assert r[0].available_at is None
    assert r[0].quality=='missing'
    assert r[0].raw['close_price']==11 and r[0].raw['request_id']=='test-request'

def test_provider_failure_is_not_demo(monkeypatch):
    monkeypatch.setenv('FUYAO_API_KEY','test-not-secret')
    for payload in [{'code':4001,'data':{}},{'code':0,'data':{'item':[]}},{'code':0,'data':{'item':[{'date_ms':'bad','close_price':None}]}}]:
        with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=payload))) as c:
            with pytest.raises(ProviderError): fetch_fuyao('600000.SH',START,END,c)

@pytest.mark.parametrize('payload',[[],{'code':0,'data':{'item':[{'date_ms':1709251200000,'close_price':'garbage'}]}},{'code':0,'data':{'item':None}}])
def test_corrupt_provider_container_is_controlled(monkeypatch,payload):
    monkeypatch.setenv('FUYAO_API_KEY','test-not-secret')
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json=payload))) as c:
        with pytest.raises(ProviderError): fetch_fuyao('600000.SH',START,END,c)
