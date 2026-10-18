import os
import re
from datetime import datetime, timezone
from contextlib import nullcontext
from decimal import Decimal, InvalidOperation
import httpx
from .models import Evidence

BASE='https://fuyao.aicubes.cn'
class ProviderError(ValueError): pass

def provider_status():
    configured=bool(os.getenv('FUYAO_API_KEY'))
    return [dict(name='扶摇金融数据',status='configured' if configured else 'unavailable',url=BASE+'/docs/',detail='历史日线适配器已实现；'+('密钥已配置，需实际调用验证。' if configured else '未配置 FUYAO_API_KEY，未调用真实行情。')+'历史首次可得时间缺失时不进入事前结论。',last_success=None),dict(name='iFinD MCP',status='unavailable',url='https://mcp.51ifind.com/',detail='当前没有可调用的已授权 iFinD MCP 工具；可导入用户合法获得的证据。',last_success=None)]

def fetch_fuyao(symbol: str, start: datetime, end: datetime, client=None) -> list[Evidence]:
    key=os.getenv('FUYAO_API_KEY')
    if not key: raise ProviderError('扶摇未配置：需要服务端 FUYAO_API_KEY')
    if not re.fullmatch(r'\d{6}\.(SH|SZ|BJ)',symbol): raise ProviderError('请输入单只 A 股 thscode，例如 600000.SH')
    if start.tzinfo is None or end.tzinfo is None or not 0<(end-start).total_seconds()<=366*86400: raise ProviderError('时间范围必须为含时区的正区间，首版最多 366 天')
    now=datetime.now(timezone.utc)
    url=BASE+'/api/a-share/prices/historical'
    params=dict(thscode=symbol,interval='1d',start=int(start.timestamp()*1000),end=int(end.timestamp()*1000),adjust='none')
    try:
        with (nullcontext(client) if client else httpx.Client(timeout=20,follow_redirects=False,trust_env=False)) as c:
            resp=c.get(url,params=params,headers={'X-api-key':key}); resp.raise_for_status()
            if len(resp.content)>2000000: raise ProviderError('行情响应过大，未写入')
            payload=resp.json()
        if not isinstance(payload,dict): raise ProviderError('扶摇响应结构无效，未写入行情')
        if payload.get('code')!=0: raise ProviderError('扶摇返回业务错误（含限流/鉴权失败），未写入行情')
        bars=payload['data']['item']
        if not isinstance(bars,list): raise ProviderError('扶摇行情列表格式无效，未写入行情')
        if not bars: raise ProviderError('扶摇没有返回该区间行情，未生成正常结论')
        result=[]
        for bar in bars:
            if not isinstance(bar,dict): raise ProviderError('扶摇行情字段格式无效，未写入行情')
            dt=datetime.fromtimestamp(int(bar['date_ms'])/1000,timezone.utc)
            close=Decimal(str(bar['close_price']))
            if not close.is_finite() or close<=0: raise ValueError('invalid close')
            result.append(Evidence(id=f"FY-{symbol}-{int(bar['date_ms'])}",symbol=symbol,kind='market',title='扶摇历史日线 · 首次可得时间待核验',occurred_at=dt,available_at=None,collected_at=now,source='扶摇金融数据 API / 历史日线',source_url=str(httpx.URL(url,params=params)),raw=bar|{'close':str(close),'adjustment':'none','request_id':payload.get('request_id'),'upstream_ready_ms':payload['data'].get('timestamp')},unit='CNY/股',methodology='日线，不复权；volume 股，turnover 原始货币。date_ms 为行情日期，data.timestamp 为序列数据就绪时间，均不冒充历史首次公开时间；原始值可能存在历史修订。',quality='missing'))
        return result
    except ProviderError: raise
    except httpx.TimeoutException as e: raise ProviderError('扶摇调用超时，未写入行情；不会回填演示数据') from e
    except httpx.HTTPError as e: raise ProviderError('扶摇 HTTP 调用失败，未写入行情；请检查授权或稍后重试') from e
    except (KeyError,ValueError,TypeError,OverflowError,InvalidOperation) as e: raise ProviderError('扶摇字段缺失或格式冲突，未写入行情') from e
