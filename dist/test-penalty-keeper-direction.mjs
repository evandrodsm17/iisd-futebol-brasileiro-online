import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {nativePenaltyKeeperDirection} from './penalty-keeper-direction.mjs';
const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-synthetic-input.json',import.meta.url),'utf8'));
test('synthetic neutral and horizontal defender inputs match recorded keeper indices',()=>{
 assert.equal(report.runs.length,3);
 for(const run of report.runs){
  const result=nativePenaltyKeeperDirection(run.input_word,run.after_cpu);
  assert.equal(result.base,run.base);assert.equal(result.index,run.final_index);assert.ok(run.selectors.length>0);
 }
});
test('CPU result must be explicit and flag adjustment is separate',()=>{
 assert.deepEqual(nativePenaltyKeeperDirection(0x280,4),{base:4,afterCpu:4,index:9});
 assert.deepEqual(nativePenaltyKeeperDirection(0x200,1),{base:4,afterCpu:1,index:1});
 assert.throws(()=>nativePenaltyKeeperDirection(0x280),RangeError);
 assert.throws(()=>nativePenaltyKeeperDirection(0x280,5),RangeError);
});
