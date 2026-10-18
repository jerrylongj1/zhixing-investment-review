from collections import defaultdict, deque
from decimal import Decimal, ROUND_HALF_UP
from .models import Trade

def realized_result(trades: list[Trade]) -> dict:
    groups=defaultdict(list)
    for t in sorted(trades,key=lambda t:t.traded_at): groups[(t.symbol,t.currency)].append(t)
    results=[]
    for (symbol,currency),items in groups.items():
        lots=deque(); pnl=Decimal('0'); sold=Decimal('0'); warnings=[]
        for t in items:
            if t.side=='buy':
                lots.append([t.quantity,t.price+t.fee/t.quantity]); continue
            available=sum((lot[0] for lot in lots),Decimal('0'))
            if available<t.quantity:
                warnings.append(f'{t.id} 卖出数量大于已记录持仓，无法计算完整盈亏')
                # Ledger becomes indeterminate: do not invent lots or silently match later trades.
                continue
            remaining=t.quantity; cost=Decimal('0')
            while remaining:
                q,unit=lots[0]; matched=min(q,remaining)
                cost+=matched*unit; remaining-=matched; lots[0][0]-=matched
                if lots[0][0]==0: lots.popleft()
            pnl+=t.quantity*t.price-t.fee-cost; sold+=t.quantity
        results.append(dict(symbol=symbol,currency=currency,realized_pnl=None if warnings else str(pnl.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)),matched_quantity=str(sold),open_quantity=str(sum((q for q,_ in lots),Decimal('0'))),warnings=warnings))
    return dict(method='FIFO，按股数分摊买入费用；卖出费用全额计入',groups=results,note='仅已实现成交结果；不含未实现盈亏、税务调整或策略因果归因；不同标的及币种不合并。')
