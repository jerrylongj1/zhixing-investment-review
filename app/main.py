import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime
from .models import CaseCreate, ImportRequest, EvidenceImport, ReasonInput, Reason, ReviewRequest, ChecklistInput, ChecklistPatch, Trade, ProviderRequest
from .storage import Store
from .imports import preview_csv, TEMPLATE
from .demo import populate_demo
from .timeline import visible_evidence
from .reviews import build_review, snapshot_evidence, ReviewError, SECTIONS
from .calculations import realized_result
from .providers import provider_status, fetch_fuyao, ProviderError

# All mutations use same-origin JSON and a per-browser high-entropy bearer cookie.
def create_app(db_path: str = None) -> FastAPI:
    app=FastAPI(title='知行 · 投资复盘工作台',version='0.1.0')
    store=Store(db_path or os.getenv('DATABASE_PATH','data/zhixing.db'))
    app.state.store=store
    @app.middleware('http')
    async def session(request: Request, call_next):
        if request.method in ('POST','PUT','PATCH','DELETE'):
            origin=request.headers.get('origin')
            allowed_origin=os.getenv('PUBLIC_ORIGIN',str(request.base_url)).rstrip('/')
            if origin and origin.rstrip('/')!=allowed_origin:
                return JSONResponse({'detail':'跨站写入请求被拒绝'},status_code=403)
            if request.headers.get('content-type','').split(';')[0]!='application/json' and request.url.path!='/api/demo':
                return JSONResponse({'detail':'写入请求须使用 application/json'},status_code=415)
            try: size=int(request.headers.get('content-length','0'))
            except ValueError: return JSONResponse({'detail':'无效长度'},status_code=400)
            if size>1050000: return JSONResponse({'detail':'请求超过 1MB 限制'},status_code=413)
            body=await request.body()
            if len(body)>1050000: return JSONResponse({'detail':'请求超过 1MB 限制'},status_code=413)
        sid=request.cookies.get('zhixing_session','')
        fresh=not re.fullmatch(r'[a-f0-9]{64}',sid)
        if fresh: sid=secrets.token_hex(32)
        request.state.owner=hashlib.sha256(sid.encode()).hexdigest()
        response=await call_next(request)
        if fresh: response.set_cookie('zhixing_session',sid,httponly=True,samesite='lax',secure=os.getenv('COOKIE_SECURE','0')=='1',max_age=60*60*24*30)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response
    def get_case(id,request):
        c=store.get(id,request.state.owner)
        if not c: raise HTTPException(404,'案例不存在或不属于当前会话')
        return c
    @app.get('/api/health')
    def health():
        return dict(status='ok',ai_configured=bool(os.getenv('AI_API_KEY') and os.getenv('AI_MODEL')),model=os.getenv('AI_MODEL') if os.getenv('AI_API_KEY') else None,data_mode='构造样例 / 用户导入；真实数据提供方尚未接入')
    @app.get('/api/providers')
    def providers(): return provider_status()
    @app.get('/api/learning')
    def learning(request:Request):
        return [item|{'case_id':c['id'],'case_title':c['title']} for c in store.list(request.state.owner) for item in c['checklist']]
    @app.get('/api/template.csv')
    def template(): return Response('\ufeff'+TEMPLATE,media_type='text/csv',headers={'Content-Disposition':'attachment; filename=trades-template.csv'})
    @app.get('/api/cases')
    def list_cases(request:Request):
        return [dict(id=c['id'],title=c['title'],demo=c['demo'],trade_count=len(c['trades']),created_at=c['created_at']) for c in store.list(request.state.owner)]
    @app.post('/api/cases')
    def create_case(body:CaseCreate,request:Request): return store.create(body.title,request.state.owner)
    @app.post('/api/demo')
    def demo(request:Request):
        with store.lock:
            existing=[c for c in store.list(request.state.owner) if c.get('demo')]
            if existing: return existing[0]
            c=populate_demo(store.create('一次加仓决策，哪些信息当时已知？',request.state.owner,True))
            store.save(c,request.state.owner); return c
    @app.get('/api/cases/{id}')
    def read_case(id:str,request:Request):
        c=get_case(id,request)
        c['calculation']=realized_result([Trade.model_validate(t) for t in c['trades']])
        return c
    @app.post('/api/cases/{id}/imports')
    def import_trades(id:str,body:ImportRequest,request:Request):
        with store.lock:
            c=get_case(id,request); result=preview_csv(body.csv)
            existing={t['id'] for t in c['trades']}
            for t in result['valid_rows']:
                if t['id'] in existing: result['errors'].append(dict(row=None,message='交易 ID 已存在：'+t['id']))
            if body.confirm:
                if result['errors']: return JSONResponse({'detail':'存在错误，未写入任何行','preview':result},status_code=422)
                if len(c['trades'])+len(result['valid_rows'])>2000: raise HTTPException(422,'每案例最多 2000 笔交易')
                c['trades'].extend(result['valid_rows']); store.save(c,request.state.owner)
            return result
    @app.put('/api/cases/{id}/reasons/{trade_id}')
    def reason(id:str,trade_id:str,body:ReasonInput,request:Request):
        with store.lock:
            c=get_case(id,request)
            if trade_id not in {t['id'] for t in c['trades']}: raise HTTPException(404,'交易不存在')
            now=datetime.now(timezone.utc)
            if body.formed_at>now: raise HTTPException(422,'理由形成时间不能晚于现在')
            r=Reason(**body.model_dump(),recorded_at=now)
            c['reasons'][trade_id]=r.model_dump(mode='json')|{'provenance':'用户补录；服务器记录时间，不构成同期证据'}
            store.save(c,request.state.owner)
            return c['reasons'][trade_id]|{'backfilled':r.backfilled}
    @app.post('/api/cases/{id}/evidence')
    def import_evidence(id:str,body:EvidenceImport,request:Request):
        with store.lock:
            c=get_case(id,request); ids=[e.id for e in body.evidence]
            if len(set(ids))!=len(ids) or set(ids)&{e['id'] for e in c['evidence']} or any(i.startswith(('T-','R-')) for i in ids): raise HTTPException(422,'证据 ID 重复或使用保留前缀 T-/R-')
            if len(c['evidence'])+len(body.evidence)>2000: raise HTTPException(422,'每案例最多 2000 条外部证据')
            c['evidence'].extend(e.model_dump(mode='json') for e in body.evidence); store.save(c,request.state.owner)
            return dict(imported=len(ids),note='用户声明的来源和可得时间，未经独立核验')
    @app.post('/api/cases/{id}/providers/fuyao')
    def sync_fuyao(id:str,body:ProviderRequest,request:Request):
        get_case(id,request)
        try: evidence=fetch_fuyao(body.symbol,body.start,body.end)
        except ProviderError as e:
            with store.lock:
                c=get_case(id,request); c['provider_last_call']={'status':'failed','at':datetime.now(timezone.utc).isoformat(),'message':str(e)}; store.save(c,request.state.owner)
            raise HTTPException(422,str(e)) from e
        with store.lock:
            c=get_case(id,request); existing={e['id'] for e in c['evidence']}
            additions=[e.model_dump(mode='json') for e in evidence if e.id not in existing]
            if len(c['evidence'])+len(additions)>2000: raise HTTPException(422,'超过证据数量限制')
            c['evidence'].extend(additions)
            c['provider_last_call']={'status':'success','at':datetime.now(timezone.utc).isoformat(),'message':f'成功获取 {len(evidence)} 条；新增 {len(additions)} 条；首次可得时间仍待核验'}
            store.save(c,request.state.owner)
        return c['provider_last_call']
    @app.get('/api/cases/{id}/timeline')
    def timeline(id:str,request:Request,cutoff:AwareDatetime=Query(...),include_future:bool=False):
        c=get_case(id,request); all_e=snapshot_evidence(c); visible=visible_evidence(all_e,cutoff)
        visible_ids={e.id for e in visible}
        entries=all_e if include_future else visible
        result=[]
        for e in sorted(entries,key=lambda e:e.occurred_at):
            result.append(e.model_dump(mode='json')|{'known_at_cutoff':e.id in visible_ids,'sha256':hashlib.sha256(json.dumps(e.raw,sort_keys=True,ensure_ascii=False).encode()).hexdigest()})
        return dict(visible=result,hidden_count=len(all_e)-len(visible),unknown_time_count=sum(e.available_at is None for e in all_e),quality_issues=sum(e.quality!='ok' for e in all_e),cutoff=cutoff.isoformat())
    @app.post('/api/cases/{id}/reviews')
    def review(id:str,body:ReviewRequest,request:Request):
        c=get_case(id,request)
        if len(c['reviews'])>=100: raise HTTPException(422,'每案例最多保存 100 份报告')
        try: report=build_review(c,body.trade_ids,body.cutoff,body.mode)
        except ReviewError as e: raise HTTPException(422,str(e)) from e
        with store.lock:
            c=get_case(id,request); c['reviews'].append(report); store.save(c,request.state.owner)
        return report
    @app.post('/api/cases/{id}/checklist')
    def add_checklist(id:str,body:ChecklistInput,request:Request):
        with store.lock:
            c=get_case(id,request); reports=[r for r in c['reviews'] if r['id']==body.review_id]
            if not reports or not set(body.evidence_ids)<={e['id'] for e in reports[0]['evidence_snapshot']}: raise HTTPException(422,'报告或证据引用无效')
            entry=body.model_dump()|dict(id=uuid4().hex,done=False)
            c['checklist'].append(entry); store.save(c,request.state.owner); return entry
    @app.patch('/api/cases/{id}/checklist/{item_id}')
    def edit_checklist(id:str,item_id:str,body:ChecklistPatch,request:Request):
        with store.lock:
            c=get_case(id,request)
            for item in c['checklist']:
                if item['id']==item_id:
                    item.update(body.model_dump(exclude_none=True)); store.save(c,request.state.owner); return item
            raise HTTPException(404,'清单条目不存在')
    @app.get('/api/cases/{id}/export')
    def export(id:str,request:Request,format:str='json'):
        c=get_case(id,request)
        if format=='json': return Response(json.dumps(c,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename=zhixing-review.json'})
        if format!='md': raise HTTPException(422,'仅支持 json 或 md')
        def clean(s): return str(s).replace('<','&lt;').replace('>','&gt;')
        lines=['# '+clean(c['title']),'','构造案例' if c['demo'] else '用户导入；未独立核验','']
        for r in c['reviews']:
            lines.extend(['## 报告 '+r['id'],f"截止：{r['cutoff']}；模式：{r['mode']}；证据 SHA256：{r['evidence_sha256']}"])
            for s in SECTIONS:
                lines.append('### '+s)
                lines.extend('- '+clean(i['text'])+' ['+', '.join(i['evidence_ids'])+']' for i in r[s])
            lines.extend(['### 原始证据快照','```json',json.dumps(r['evidence_snapshot'],ensure_ascii=False,indent=2),'```'])
        lines.extend(['## 学习清单']+['- ['+('x' if i['done'] else ' ')+'] '+clean(i['text']) for i in c['checklist']])
        return Response('\n\n'.join(lines),media_type='text/markdown',headers={'Content-Disposition':'attachment; filename=zhixing-review.md'})
    source_root=os.getenv('PUBLIC_SOURCE_PATH')
    @app.get('/source.git')
    def source_index(request:Request):
        if not source_root: raise HTTPException(404,'未启用公开源码快照')
        return Response('Read-only Git source snapshot.\nClone: git clone '+os.getenv('PUBLIC_ORIGIN',str(request.base_url)).rstrip('/')+'/source.git\nOnly code is served; user data is excluded.\n',media_type='text/plain')
    @app.get('/source.git/{source_path:path}')
    def source_file(source_path:str):
        allowed=r'HEAD|info/refs|objects/info/packs|objects/[0-9a-f]{2}/[0-9a-f]{38}|objects/pack/pack-[0-9a-f]{40}\.(pack|idx)'
        if not source_root or not re.fullmatch(allowed,source_path): raise HTTPException(404,'源码对象不存在')
        root=Path(source_root).resolve(); target=(root/source_path).resolve()
        if not target.is_relative_to(root) or not target.is_file(): raise HTTPException(404,'源码对象不存在')
        return FileResponse(target,media_type='application/octet-stream' if source_path.startswith('objects/') else 'text/plain')
    dist=Path(__file__).resolve().parent.parent/'web'/'dist'
    if dist.exists():
        app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
        @app.get('/')
        def index(): return FileResponse(dist/'index.html')
    return app
