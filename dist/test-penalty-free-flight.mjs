import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {advanceNativePenaltyFreeFlight as advance} from './penalty-free-flight.mjs';

test('moves and applies gravity in 24-bit arithmetic without mutating input',()=>{
 const initial={x:0xfffff0,y:0x10,z:0x100,vx:0x20,vy:0xffffe0,vz:0xfffff0};
 assert.deepEqual(advance(initial,0x20),{x:0x10,y:0xfffff0,z:0xf0,vx:0x20,vy:0xffffe0,vz:0x10});
 assert.equal(initial.x,0xfffff0);
 assert.throws(()=>advance({...initial,x:-1},0x20),RangeError);
 assert.throws(()=>advance(initial,0x1000000),RangeError);
});

test('recorded free-flight low words and full velocities agree with the native step',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-free-flight.json',import.meta.url),'utf8'));
 assert.equal(report.samples.length,284);assert.equal(report.excluded_pairs.length,8);
 for(const sample of report.samples){
  const [x,y,z]=sample.position_low,[vx,vy,vz]=sample.velocity;
  // Upper position bytes were not captured; test several values without claiming they were observed.
  for(const upper of [0,0x7f0000,0xff0000]){
   const result=advance({x:x|upper,y:y|upper,z:z|upper,vx,vy,vz},report.gravity);
   assert.deepEqual([result.x&0xffff,result.y&0xffff,result.z&0xffff],sample.next_position_low,`frame ${sample.frame}`);
   assert.deepEqual([result.vx,result.vy,result.vz],sample.next_velocity,`frame ${sample.frame}`);
  }
 }
});
