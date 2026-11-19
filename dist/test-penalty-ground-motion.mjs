import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {advanceNativePenaltyGroundStep as step} from './penalty-ground-motion.mjs';

test('matches the six captured damping and bounce transitions',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-flight-differences.json',import.meta.url),'utf8'));
 assert.equal(report.results.length,8);
 let applied=0;
 for(const sample of report.results){
  if(sample.route==='object_contact')continue;
  const [x,y,z]=sample.position_low,[vx,vy,vz]=sample.velocity;
  const result=step({x,y,z,vx,vy,vz},0x20,{frictionX:sample.friction_x,frictionY:sample.friction_y,bounce:sample.route==='ground_contact'});
  assert.deepEqual([result.x&0xffff,result.y&0xffff,result.z&0xffff],sample.next_position_low,`frame ${sample.frame}`);
  assert.deepEqual([result.vx,result.vy,result.vz],sample.next_velocity,`frame ${sample.frame}`);
  applied++;
 }
 assert.equal(applied,6);
 assert.equal(report.results.filter(item=>item.route==='object_contact').length,2);
});

test('caller controls friction and contact; no implicit collision is inferred',()=>{
 const state={x:100,y:200,z:300,vx:3,vy:0xfffffd,vz:10};
 const unchanged=step(state,32,{frictionX:false,frictionY:false,bounce:false});
 assert.deepEqual(unchanged,{x:103,y:197,z:310,vx:3,vy:0xfffffd,vz:42});
 const slowed=step(state,32,{frictionX:true,frictionY:true,bounce:true});
 assert.equal(slowed.vx,0xfffffb);assert.equal(slowed.vy,5);
 assert.equal(slowed.z,54);assert.equal(slowed.vz,0xffffeb);
 assert.throws(()=>step(state,32,{frictionX:true,frictionY:false}),RangeError);
 assert.throws(()=>step({...state,vz:0xffff00},32,{frictionX:false,frictionY:false,bounce:true}),RangeError);
});

import {advanceNativePenaltyMotion as automatic} from './penalty-ground-motion.mjs';
test('native word gates distinguish airborne, ground and bounce',()=>{
 const base={x:0x008000,y:0x008000,z:0xffff00,vx:0x100,vy:0xffff00,vz:0x80};
 const air=automatic(base,0x20,{stopAfter:false});
 assert.equal(air.z,0xffff80);assert.equal(air.vx,base.vx);assert.equal(air.vy,base.vy);assert.equal(air.vz,0xa0);
 const ground=automatic({...base,z:0xffff80},0x20,{stopAfter:false});
 assert.equal(ground.z,0);assert.equal(ground.vx,0xf8);assert.equal(ground.vy,0xffff08);assert.equal(ground.vz,0xa0);
 const bounce=automatic({...base,z:0xffff00,vz:0x200},0x20,{stopAfter:false});
 assert.equal(bounce.z,0);assert.equal(bounce.vx,0xf8);assert.equal(bounce.vy,0xffff08);assert.equal(bounce.vz,0xfffef0);
});
test('stop routine is opt-in and follows low-word thresholds',()=>{
 const state={x:0x100,y:0x100,z:0,vx:0,vy:0,vz:0};
 assert.deepEqual(automatic(state,0x20,{stopAfter:false}),{x:0x100,y:0x100,z:0,vx:0xfffff8,vy:0xfffff8,vz:0x20});
 assert.deepEqual(automatic(state,0x20,{stopAfter:true}),{x:0x100,y:0x100,z:0,vx:0,vy:0,vz:0});
 assert.throws(()=>automatic(state,0x20,{}),RangeError);
});

test('automatic native gates reproduce all eight full captured motion states',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-ground-gates.json',import.meta.url),'utf8'));
 assert.equal(report.results.length,8);
 for(const sample of report.results){
  const motion=automatic(sample.before,sample.gravity,{stopAfter:false});
  assert.deepEqual(motion,sample.after_motion,`motion frame ${sample.frame}`);
  if(sample.stop_after){
   const stopped=automatic(sample.before,sample.gravity,{stopAfter:true});
   assert.deepEqual(stopped,sample.after_stop,`stop frame ${sample.frame}`);
  }
 }
 assert.equal(report.results.filter(sample=>sample.branches.bounce).length,4);
 assert.equal(report.results.filter(sample=>sample.stop_after).length,2);
});
