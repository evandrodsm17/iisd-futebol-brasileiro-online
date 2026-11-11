import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {nativeType5InitialVerticalVelocity} from './native-shot-type5.mjs';
const values=[-.25,-.25,-.5,-.75,-1.25,-1.5,-1.75,-2,-2,-2.25,-2.25,-2.5];
function signed(v){const raw=(v.integer<<16)|v.fraction;return raw/65536;}
test('returns observed type-5 vertical values and rejects invalid parameters',()=>{
 assert.deepEqual(values.map((_,i)=>signed(nativeType5InitialVerticalVelocity(i))),values);
 for(const invalid of [-1,12,1.5,NaN])assert.throws(()=>nativeType5InitialVerticalVelocity(invalid),RangeError);
});
const rom=new URL('../International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc',import.meta.url);
test('all 24 words match the local USA ROM',{skip:!existsSync(rom)},()=>{
 const bytes=readFileSync(rom);
 for(let i=0;i<12;i++)assert.deepEqual(nativeType5InitialVerticalVelocity(i),{integer:bytes.readUInt16LE(0xa24b+2*i),fraction:bytes.readUInt16LE(0xa263+2*i)});
});
const trace=new URL('../analysis/shot-hold-full/trace.jsonl',import.meta.url);
test('matches releases observed across 15 local hold trials',{skip:!existsSync(trace)},()=>{
 const rows=readFileSync(trace,'utf8').trim().split(/\r?\n/).map(JSON.parse);let count=0;const seen=new Set();
 for(const hook of rows.filter(r=>r.type==='hook'&&r.site==='85F89B')){
  const frame=rows.find(r=>r.type==='frame'&&r.trial===hook.trial&&r.step===hook.step);
  assert.ok(frame);assert.equal(frame.ballType,5);
  assert.deepEqual(nativeType5InitialVerticalVelocity(hook.y),{integer:frame.vz,fraction:frame.vzFrac});seen.add(hook.y);count++;
 }
 assert.equal(count,15);assert.equal(seen.size,12);
});
