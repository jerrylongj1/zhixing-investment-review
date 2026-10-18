from .models import Trade, Evidence

def populate_demo(case):
    case['trades']=[Trade(id=id,symbol='DEMO.A',side=side,quantity=q,price=p,fee=fee,currency='CNY',traded_at=time).model_dump(mode='json') for id,side,q,p,fee,time in [
        ('D1','buy','1000','10.00','5','2024-03-04T10:15:00+08:00'),
        ('D2','buy','500','10.80','5','2024-03-06T14:20:00+08:00'),
        ('D3','sell','800','9.60','5','2024-03-12T10:30:00+08:00')]]
    case['reasons']={'D1':dict(text='收入增长可能改善基本面；尚未明确毛利率下降是否持续。',formed_at='2024-03-04T10:00:00+08:00',recorded_at='2024-03-04T10:00:00+08:00',expectation='下个季度验证收入与利润同步变化。',invalidation='若毛利率持续下降，重新审查原假设。',provenance='构造样例中的同期记录，不是真实历史证据'),
        'D2':dict(text='价格上涨后增加仓位，担心错过；未补充新的经营证据。',formed_at='2024-03-06T14:00:00+08:00',recorded_at='2024-03-15T09:00:00+08:00',expectation='',invalidation='',provenance='构造样例，事后补录')}
    def ev(id,kind,title,occurred,available,raw,unit,quality='ok'):
        return Evidence(id=id,symbol='DEMO.A',kind=kind,title=title,occurred_at=occurred,available_at=available,collected_at='2024-03-18T09:00:00+08:00',source='知行构造样例 · 非真实证券/行情',raw=raw,unit=unit,methodology='为演示时点隔离而构造；未接入行情 API，不可用于投资',quality=quality).model_dump(mode='json')
    case['evidence']=[
        ev('E1','event','经营简报：收入增长，毛利率承压','2024-03-01T00:00:00+08:00','2024-03-01T18:00:00+08:00',{'revenue_yoy_pct':12.4,'gross_margin_pct':23.1,'text':'构造经营简报：收入同比增长 12.4%，毛利率 23.1%。收入增长不等于利润改善。'},'%'),
        ev('E2','market','首笔交易前一交易日收盘快照','2024-03-01T15:00:00+08:00','2024-03-01T15:05:00+08:00',{'close':'9.85','adjustment':'不复权','text':'构造收盘价 9.85 元；单位 CNY/股。'},'CNY/股'),
        ev('E3','market','首笔交易当日收盘：盘中尚不可知','2024-03-04T15:00:00+08:00','2024-03-04T15:05:00+08:00',{'close':'10.30','adjustment':'不复权','text':'10:15 决策时不能使用当日完整收盘价。'},'CNY/股'),
        ev('E4','event','后续公告：成本压力仍待验证','2024-03-08T18:00:00+08:00','2024-03-08T18:00:00+08:00',{'text':'构造公告：成本压力延续。不能据此断言当初应当预见。'},'不适用'),
        ev('E5','market','后续收盘快照','2024-03-12T15:00:00+08:00','2024-03-12T15:05:00+08:00',{'close':'9.50','adjustment':'不复权'},'CNY/股'),
        ev('E6','event','未经核实的市场传闻','2024-03-03T09:00:00+08:00',None,{'text':'首次公开时间不明，不得认定为事前可知。'},'不适用','missing')]
    return case
