from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, AwareDatetime, ConfigDict, model_validator, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Reason(StrictModel):
    text: str = Field(min_length=1, max_length=4000)
    formed_at: AwareDatetime
    recorded_at: AwareDatetime
    expectation: str = Field(default='', max_length=2000)
    invalidation: str = Field(default='', max_length=2000)
    @property
    def backfilled(self):
        return self.recorded_at > self.formed_at

class Trade(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    symbol: str = Field(min_length=1, max_length=30)
    side: Literal['buy','sell']
    quantity: Annotated[Decimal, Field(gt=0, le=1000000000, allow_inf_nan=False)]
    price: Annotated[Decimal, Field(gt=0, le=1000000000, allow_inf_nan=False)]
    fee: Annotated[Decimal, Field(ge=0, le=1000000000, allow_inf_nan=False)] = Decimal('0')
    currency: Literal['CNY','USD','HKD'] = 'CNY'
    traded_at: AwareDatetime

class Evidence(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    symbol: str = Field(min_length=1, max_length=30)
    kind: Literal['event','market','reason','trade'] = 'event'
    title: str = Field(min_length=1, max_length=300)
    occurred_at: AwareDatetime
    available_at: Optional[AwareDatetime] = None
    collected_at: AwareDatetime
    source: str = Field(min_length=1, max_length=300)
    source_url: Optional[str] = Field(default=None, max_length=2000)
    raw: dict
    unit: str = Field(min_length=1,max_length=100)
    methodology: str = Field(min_length=1,max_length=1000)
    quality: Literal['ok','missing','conflict','stale','failed'] = 'ok'
    @field_validator('source_url')
    @classmethod
    def safe_url(cls,v):
        if v:
            from urllib.parse import urlparse
            p=urlparse(v)
            if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:
                raise ValueError('来源链接必须为 HTTP(S)，不能含凭据')
        return v

class CaseCreate(StrictModel):
    title: str = Field(min_length=1, max_length=100)

class ImportRequest(StrictModel):
    csv: str = Field(max_length=1000000)
    confirm: bool = False

class EvidenceImport(StrictModel):
    evidence: list[Evidence] = Field(max_length=500)

class ReasonInput(StrictModel):
    text: str = Field(min_length=1,max_length=4000)
    formed_at: AwareDatetime
    expectation: str = Field(default='',max_length=2000)
    invalidation: str = Field(default='',max_length=2000)

class ReviewRequest(StrictModel):
    cutoff: AwareDatetime
    trade_ids: list[str] = Field(min_length=1,max_length=100)
    mode: Literal['rules','ai'] = 'rules'

class ReviewItem(StrictModel):
    text: str = Field(min_length=1,max_length=2000)
    evidence_ids: list[str] = Field(min_length=1,max_length=50)
    decision_ids: list[str] = Field(min_length=1,max_length=100)

class ReviewContent(StrictModel):
    facts: list[ReviewItem] = Field(min_length=1,max_length=220)
    hypotheses: list[ReviewItem] = Field(max_length=220)
    bias_signals: list[ReviewItem] = Field(max_length=220)
    uncertainties: list[ReviewItem] = Field(min_length=1,max_length=220)
    improvements: list[ReviewItem] = Field(min_length=1,max_length=220)

class ChecklistInput(StrictModel):
    text: str = Field(min_length=1,max_length=2000)
    review_id: str
    evidence_ids: list[str] = Field(min_length=1,max_length=50)

class ChecklistPatch(StrictModel):
    text: Optional[str] = Field(default=None,min_length=1,max_length=2000)
    done: Optional[bool] = None

class ProviderRequest(StrictModel):
    symbol: str = Field(min_length=1,max_length=30)
    start: AwareDatetime
    end: AwareDatetime
