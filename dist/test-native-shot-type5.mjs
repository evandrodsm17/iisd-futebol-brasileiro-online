import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {nativeType5InitialVerticalVelocity,nativeType5AuxiliaryFields} from './native-shot-type5.mjs';
const values=[-.25,-.25,-.5,-.75,-1.25,-1.5,-1.75,-2,-2,-2.25,-2.25,-2.5];
function signed(v){const raw=(v.integer<<16)|v.fraction;return raw/65536;}
test('returns observed type-5 vertical values and rejects invalid parameters',()=>{
 assert.deepEqual(values.map((_,i)=>signed(nativeType5InitialVerticalVelocity(i))),values);
 for(const invalid of [-1,12,1.5,NaN])assert.throws(()=>nativeType5InitialVerticalVelocity(invalid),RangeError);
});
test('initializes auxiliary words with the context nibble saturated at nine',()=>{
 assert.deepEqual(nativeType5AuxiliaryFields(0,0),{field54:0,field58:0x1000});
 assert.deepEqual(nativeType5AuxiliaryFields(11,0xffff),{field54:28,field58:0x2000});
 assert.deepEqual(nativeType5AuxiliaryFields(6,0x1238),{field54:18,field58:0x1c00});
 for(const invalid of [-1,12,1.5,NaN])assert.throws(()=>nativeType5AuxiliaryFields(invalid,0),RangeError);
 for(const invalid of [-1,65536,1.5,NaN])assert.throws(()=>nativeType5AuxiliaryFields(0,invalid),RangeError);
});
const rom=new URL('../International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc',import.meta.url);
test('all 24 words match the local USA ROM',{skip:!existsSync(rom)},()=>{
 const bytes=readFileSync(rom);
 for(let i=0;i<12;i++)assert.deepEqual(nativeType5InitialVerticalVelocity(i),{integer:bytes.readUInt16LE(0xa24b+2*i),fraction:bytes.readUInt16LE(0xa263+2*i)});
});
test('all auxiliary field combinations match the three local ROM tables',{skip:!existsSync(rom)},()=>{
 const bytes=readFileSync(rom);
 for(let parameter=0;parameter<12;parameter++)for(let nibble=0;nibble<16;nibble++){
  assert.deepEqual(nativeType5AuxiliaryFields(parameter,0xfff0|nibble),{
   field54:bytes.readUInt16LE(0xa233+2*parameter)+bytes.readUInt16LE(0xa293+2*Math.min(nibble,9)),
   field58:bytes.readUInt16LE(0xa27b+2*parameter),
  });
 }
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
