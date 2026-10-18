from decimal import Decimal
from app.models import Trade
from app.calculations import realized_result

def trade(id,side,q,p,fee='1',symbol='DEMO',currency='CNY'):
    return Trade(id=id,symbol=symbol,side=side,quantity=q,price=p,fee=fee,currency=currency,traded_at=f'2024-01-0{1 if side=="buy" else 2}T10:00:00+08:00')

def test_partial_sell_and_fees():
    r=realized_result([trade('b','buy','100','10'),trade('s','sell','40','12')])
    assert r['groups'][0]['realized_pnl']=='78.60'
    assert r['method']=='FIFO，按股数分摊买入费用；卖出费用全额计入'

def test_unmatched_and_currency_separation():
    assert realized_result([trade('s','sell','40','12')])['groups'][0]['realized_pnl'] is None
    r=realized_result([trade('b','buy','100','10'),trade('s','sell','40','12',currency='USD')])
    assert len(r['groups'])==2
    assert r['groups'][1]['realized_pnl'] is None
