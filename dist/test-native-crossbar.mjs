import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync,readFileSync } from 'node:fs';
import { nativeCrossbarCandidate,nativeCrossbarHorizontalResponse } from './native-crossbar.mjs';
const base={stadium:1,width:1856,x:0,y:320,height:0xffc0,velocityXHigh:1,globalBA:0};
test('matches central band, height and both native line boundaries',()=>{
 for(const x of [0xfffc,0xffff,0,3,1852,1856,1860])assert.equal(nativeCrossbarCandidate({...base,x}).response,true,`x=${x}`);
 for(const x of [0xfffb,4,1851,1861])assert.equal(nativeCrossbarCandidate({...base,x}).response,false,`x=${x}`);
 for(const h of [0xffbf,0xffc8,0,0x7fff])assert.equal(nativeCrossbarCandidate({...base,height:h}).response,false);
 assert.equal(nativeCrossbarCandidate({...base,height:0xffc7}).response,true);
 for(const y of [271,368])assert.equal(nativeCrossbarCandidate({...base,y}).response,false);
 for(const y of [272,367])assert.equal(nativeCrossbarCandidate({...base,y}).response,true);
 assert.equal(nativeCrossbarCandidate({...base,globalBA:1}).audioCommand,null);
 assert.equal(nativeCrossbarCandidate({...base,velocityXHigh:0}).audioCommand,null);
 assert.equal(nativeCrossbarCandidate(base).audioCommand,44);
});
test('models signed 16.16 response and minimum word without rounding up',()=>{
 assert.deepEqual(nativeCrossbarHorizontalResponse({x:1851,vxHigh:1,vxLow:61026,vyHigh:0}),{high:0xffff,low:0});
 assert.deepEqual(nativeCrossbarHorizontalResponse({x:1851,vxHigh:3,vxLow:62830,vyHigh:0}),{high:0xfffe,low:1353});
 assert.deepEqual(nativeCrossbarHorizontalResponse({x:5,vxHigh:0xfffe,vxLow:1865,vyHigh:0}),{high:0,low:64603});
 assert.deepEqual(nativeCrossbarHorizontalResponse({x:0xfffc,vxHigh:0,vxLow:1,vyHigh:0}),{high:1,low:0});
 assert.deepEqual(nativeCrossbarHorizontalResponse({x:0,vxHigh:0,vxLow:1,vyHigh:0xffff}),{high:0xffff,low:0});
 assert.throws(()=>nativeCrossbarHorizontalResponse({x:-1,vxHigh:0,vxLow:0,vyHigh:0}),RangeError);
});
const files=['../analysis/goal-velocity-right/trace.jsonl','../analysis/goal-velocity-left-fresh/trace.jsonl'];
test('agrees with recorded pre/post subroutine velocity in both local replays', {skip:!files.every(p=>existsSync(new URL(p,import.meta.url)))},()=>{
 let verified=0;
 for(const file of files){const rows=readFileSync(new URL(file,import.meta.url),'utf8').trim().split(/\r?\n/).map(JSON.parse);
  for(const row of rows.filter(r=>r.type==='hook'&&r.pc==='838C51')){
   const after=rows.find(r=>r.type==='hook'&&r.trial===row.trial&&r.step===row.step&&r.pc==='83A900');
   if(!after)continue;
   assert.deepEqual(nativeCrossbarHorizontalResponse({x:row.local2a,vxHigh:row.vx,vxLow:row.vxLo,vyHigh:row.vy}),{high:after.vx,low:after.vxLo});verified++;
  }
 }
 assert.ok(verified>=12,`expected at least 12 response pairs, got ${verified}`);
});
test('matches branch observations in the local 25-case replay',{skip:!existsSync(new URL('../analysis/goal-camera-matrix-detail/trace.jsonl',import.meta.url))},()=>{
 const rows=readFileSync(new URL('../analysis/goal-camera-matrix-detail/trace.jsonl',import.meta.url),'utf8').trim().split(/\r?\n/).map(JSON.parse);
 let checked=0,responses=0;
 for(let i=0;i<rows.length;i++){
  const r=rows[i];if(r.type!=='hook'||r.pc!=='838B47')continue;
  const subsequent=[];
  for(let j=i+1;j<rows.length&&rows[j].trial===r.trial&&rows[j].step===r.step&&rows[j].type==='hook';j++)subsequent.push(rows[j]);
  const observed=subsequent.some(row=>row.pc==='838B75');
  const actual=nativeCrossbarCandidate({stadium:1,width:1856,x:r.local2a,y:r.local2c,height:r.z,velocityXHigh:r.vx,globalBA:0}).response;
  assert.equal(actual,observed,`trial ${r.trial}, frame ${r.step}`);checked++;if(observed)responses++;
 }
 assert.ok(checked>=10);assert.ok(responses>=2);
});
