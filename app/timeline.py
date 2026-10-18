from datetime import datetime
from .models import Evidence

def visible_evidence(evidence: list[Evidence], cutoff: datetime) -> list[Evidence]:
    if cutoff.tzinfo is None:
        raise ValueError('截止时间必须包含时区')
    return sorted([e for e in evidence if e.available_at is not None and e.available_at <= cutoff],key=lambda e:e.available_at)
