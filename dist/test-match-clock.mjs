import assert from 'node:assert/strict';
import { decrementMatchBcd } from './match-clock.mjs';
for (const [input, expected] of [[0x0500,0x0459],[0x0450,0x0449],[0x0410,0x0409],[0x0401,0x0400],[0x0100,0x0059],[0x0001,0x0000],[0x0000,0x0000]]) assert.equal(decrementMatchBcd(input), expected);
let value=0x0500;
for(let i=0;i<300;i++) value=decrementMatchBcd(value);
assert.equal(value,0);
assert.throws(()=>decrementMatchBcd(0x04bf),RangeError);
console.log('OK: contagem BCD e transições do relógio');
