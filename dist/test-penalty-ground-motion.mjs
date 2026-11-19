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
