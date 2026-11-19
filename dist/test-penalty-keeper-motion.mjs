import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {advanceNativePenaltyKeeper} from './penalty-keeper-motion.mjs';
const report=JSON.parse(readFileSync(new URL('./data/issd-penalty-keeper-motion.json',import.meta.url),'utf8'));
test('native keeper movement matches 107 instrumented calls',()=>{
 let count=0;for(const capture of report.captures)for(const sample of capture.samples){
  assert.deepEqual(advanceNativePenaltyKeeper(sample.before,sample.linked_flags),sample.after,`${capture.direction} frame ${sample.frame}`);count++;
 }
 assert.equal(count,107);
});
test('linked ground branch and airborne branch preserve distinct behavior',()=>{
 const state={x:0x8000,y:0x6400,z:0,vx:512,vy:32,vz:0};
 assert.deepEqual(advanceNativePenaltyKeeper(state,2),{...state,x:0x8200,y:0x6420});
 assert.deepEqual(advanceNativePenaltyKeeper({...state,vz:0xfffe00},2),{...state,x:0x8200,y:0x6420,z:0xfffe00,vz:0xfffe38});
 assert.throws(()=>advanceNativePenaltyKeeper({...state,x:-1},2),RangeError);
});
