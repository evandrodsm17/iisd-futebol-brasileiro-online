import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {updateNativeActionCharge} from './native-action-charge.mjs';
test('counts held input, freezes on release and clears at the native limit',()=>{
 assert.deepEqual(updateNativeActionCharge({held:0x40,mask:0x40,count:0}),{mask:0x40,count:1});
 assert.deepEqual(updateNativeActionCharge({held:0,mask:0x40,count:5}),{mask:0,count:5});
 assert.deepEqual(updateNativeActionCharge({held:0x40,mask:0x40,count:10}),{mask:0x40,count:11});
 assert.deepEqual(updateNativeActionCharge({held:0x40,mask:0x40,count:11}),{mask:0,count:11});
 assert.throws(()=>updateNativeActionCharge({held:-1,mask:64,count:0}),RangeError);
});
const path=new URL('../analysis/shot-charge-left/charge-hooks.jsonl',import.meta.url);
test('observed held-X sequence agrees with the fixed-word update',{skip:!existsSync(path)},()=>{
 const rows=readFileSync(path,'utf8').trim().split(/\r?\n/).map(JSON.parse).filter(r=>r.site==='80DA68'&&r.frame>=4276&&r.frame<=4282);
 assert.equal(rows.length,7);
 for(let i=0;i<rows.length-1;i++){
  const row=rows[i],next=rows[i+1];
  assert.deepEqual(updateNativeActionCharge({held:row.heldP2,mask:row.mask,count:row.charge}),{mask:next.mask,count:next.charge});
 }
});
