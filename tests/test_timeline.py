from datetime import datetime
import pytest
from app.models import Evidence, Reason
from app.timeline import visible_evidence

def evidence(**kw):
    return Evidence(**(dict(id='e1', symbol='DEMO', kind='event', title='公告', occurred_at='2024-01-01T09:00:00+08:00', available_at='2024-01-01T10:00:00+08:00', collected_at='2024-01-02T10:00:00+08:00', source='构造样例', raw={'text':'测试'}, unit='不适用', methodology='构造') | kw))

def test_cutoff_exact_and_later():
    items=[evidence(),evidence(id='later',available_at='2024-01-01T10:00:01+08:00'),evidence(id='unknown',available_at=None)]
    assert [e.id for e in visible_evidence(items,datetime.fromisoformat('2024-01-01T02:00:00+00:00'))]==['e1']

def test_naive_time_rejected():
    with pytest.raises(ValueError): evidence(available_at='2024-01-01T10:00:00')

def test_reason_backfill():
    r=Reason(text='看好',formed_at='2024-01-01T10:00:00+08:00',recorded_at='2024-02-01T10:00:00+08:00')
    assert r.backfilled is True

def test_unsafe_source_url():
    with pytest.raises(ValueError): evidence(source_url='javascript:alert(1)')
