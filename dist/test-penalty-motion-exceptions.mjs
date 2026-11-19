import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {projectPenaltyAfterFreeFlight,projectPenaltyAfterObservedBounce} from './penalty-motion-projection.mjs';
const data=JSON.parse(readFileSync(new URL('./data/issd-penalty-motion-exceptions.json',import.meta.url),'utf8'));
test('goal crossings and bounces reproduce recorded OAM and verified state fields',()=>{
 const counts={goal_crossing:0,ground_bounce:0};
 for(const capture of data.captures)for(const sample of capture.cases){
  const {before,after,partX,partY,size,oamX,oamY,kind}=sample;
  const project=kind==='ground_bounce'?projectPenaltyAfterObservedBounce:projectPenaltyAfterFreeFlight;
  const actual=project(before,data.gravity,{partX,partY,size});
  assert.deepEqual(actual.oam,{x:oamX,y:oamY});
  assert.deepEqual([actual.state.x&65535,actual.state.y&65535,actual.state.z&65535],[after.x,after.y,after.z]);
  assert.equal(actual.state.vz,after.vz);
  if(kind==='ground_bounce')assert.deepEqual([actual.state.vx,actual.state.vy],[after.vx,after.vy]);
  else assert.deepEqual([after.vx,after.vy],[0,0]);
  counts[kind]++;
 }
 assert.deepEqual(counts,{goal_crossing:2,ground_bounce:2});
});
test('bounce model rejects unobserved horizontal movement',()=>{
 assert.throws(()=>projectPenaltyAfterObservedBounce({vx:1,vy:0},32,{size:8,partX:0,partY:0}),RangeError);
});
