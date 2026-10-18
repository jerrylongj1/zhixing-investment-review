export type Trade={id:string;symbol:string;side:'buy'|'sell';quantity:string;price:string;fee:string;currency:string;traded_at:string};
export type Evidence={id:string;symbol:string;kind:string;title:string;occurred_at:string;available_at:string|null;collected_at:string;source:string;source_url?:string;raw:Record<string,unknown>;unit:string;methodology:string;quality:string;known_at_cutoff?:boolean;sha256?:string};
export type Reason={text:string;formed_at:string;recorded_at:string;expectation:string;invalidation:string;provenance:string};
export type Item={text:string;evidence_ids:string[];decision_ids:string[]};
export const sections=['facts','hypotheses','bias_signals','uncertainties','improvements'] as const;
export type Section=typeof sections[number];
export type Review=Record<Section,Item[]>&{id:string;mode:string;model:string|null;cutoff:string;created_at:string;evidence_snapshot:Evidence[];evidence_sha256:string;validation:string;trade_ids:string[]};
export type Checklist={id:string;text:string;done:boolean;review_id:string;evidence_ids:string[]};
export type Calculation={groups:{symbol:string;currency:string;realized_pnl:string|null;open_quantity:string;warnings:string[]}[];method:string;note:string};
export type Case={id:string;title:string;demo:boolean;trades:Trade[];reasons:Record<string,Reason>;evidence:Evidence[];reviews:Review[];checklist:Checklist[];provider_last_call?:{status:string;at:string;message:string};calculation?:Calculation};
export type CaseSummary={id:string;title:string;demo:boolean;trade_count:number};
export type Timeline={visible:Evidence[];hidden_count:number;unknown_time_count:number;quality_issues:number};
export type Health={status:string;ai_configured:boolean;model:string|null;data_mode:string};
export type Provider={name:string;status:string;detail:string;url:string};
export async function api<T>(url:string,options:RequestInit={}):Promise<T>{
 const res=await fetch('/api'+url,{...options,headers:{'Content-Type':'application/json',...options.headers}});
 const data=await res.json();
 if(!res.ok){const detail=data.detail;throw new Error(typeof detail==='string'?detail:Array.isArray(detail)?detail.map((d:{msg:string})=>d.msg).join('；'):'请求失败，请核对输入后重试');}
 return data;
}
export const post=<T,>(url:string,body:unknown={})=>api<T>(url,{method:'POST',body:JSON.stringify(body)});
export const date=(time:string|null)=>time?new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(time)):'时点待核验';
export const fullDate=(time:string)=>new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(time));
export function localDate(time:string){const d=new Date(time);return new Date(d.getTime()+8*3600000).toISOString().slice(0,19)}

export function withZone(local:string){return local+(local.length===16?':00':'')+'+08:00'}
