import csv
import io
from pydantic import ValidationError
from .models import Trade

COLUMNS=['id','symbol','side','quantity','price','fee','currency','traded_at']
TEMPLATE=','.join(COLUMNS)+'\nt1,DEMO,buy,100,10.00,1.00,CNY,2024-01-02T10:00:00+08:00\n'

def preview_csv(text: str) -> dict:
    rows,errors=[],[]
    if len(text.encode('utf-8'))>1000000:
        return dict(valid_rows=[],errors=[dict(row=0,message='文件超过 1MB')])
    try:
        reader=csv.DictReader(io.StringIO(text.lstrip('\ufeff')),strict=True)
        if reader.fieldnames != COLUMNS:
            return dict(valid_rows=[],errors=[dict(row=1,message='CSV 表头必须依次为：'+','.join(COLUMNS))])
        seen=set()
        for n,row in enumerate(reader,2):
            if n>1001:
                errors.append(dict(row=n,message='最多导入 1000 行')); break
            try:
                t=Trade.model_validate(row)
                if t.id in seen: raise ValueError('重复交易 ID')
                seen.add(t.id)
                rows.append(t.model_dump(mode='json'))
            except (ValueError,ValidationError) as e:
                errors.append(dict(row=n,message=str(e)[:400]))
    except csv.Error as e:
        errors.append(dict(row=0,message='CSV 格式无效：'+str(e)))
    if not rows and not errors: errors.append(dict(row=2,message='文件没有交易记录'))
    return dict(valid_rows=rows,errors=errors)
