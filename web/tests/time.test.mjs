import test from 'node:test';
import assert from 'node:assert/strict';
import {localDate,withZone} from '../src/api.ts';

test('回到此刻保留成交秒数，不回到交易之前',()=>{
 const local=localDate('2024-03-04T02:15:30Z');
 assert.equal(local,'2024-03-04T10:15:30');
 assert.equal(new Date(withZone(local)).getTime(),new Date('2024-03-04T02:15:30Z').getTime());
});
test('分钟输入与秒输入都只附加一次时区',()=>{
 assert.equal(withZone('2024-03-04T10:15'),'2024-03-04T10:15:00+08:00');
 assert.equal(withZone('2024-03-04T10:15:30'),'2024-03-04T10:15:30+08:00');
});
