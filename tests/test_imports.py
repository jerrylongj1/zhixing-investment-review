from app.imports import preview_csv
HEADER='id,symbol,side,quantity,price,fee,currency,traded_at\n'
def test_csv_valid_and_duplicate():
    row='t1,DEMO,buy,100,10,1,CNY,2024-01-01T10:00:00+08:00\n'
    r=preview_csv(HEADER+row+row)
    assert len(r['valid_rows'])==1
    assert r['errors'][0]['row']==3

def test_invalid_values_and_naive_time():
    for quantity,time in [('-1','2024-01-01T10:00:00+08:00'),('NaN','2024-01-01T10:00:00+08:00'),('1','2024-01-01T10:00:00')]:
        r=preview_csv(HEADER+f't1,DEMO,buy,{quantity},10,0,CNY,{time}\n')
        assert not r['valid_rows'] and r['errors']

def test_empty_and_limit():
    assert preview_csv('')['errors']
    assert preview_csv('x'*1000001)['errors']
