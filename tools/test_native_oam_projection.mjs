import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeOamProjectionBase as project} from './native_oam_projection.mjs';

test('base uses the wrapped native sum of depth and height',()=>{
 assert.deepEqual(project({x:128,y:90,height:0xffd9}),{x8:124,y8:47,x16:120,y16:43});
 assert.deepEqual(project({x:0,y:1,height:0}),{x8:65532,y8:65533,x16:65528,y16:65529});
 assert.throws(()=>project({x:0,y:1,height:-1}),RangeError);
});

import {readFileSync} from 'node:fs';
test('all two-frame candidates in this capture have the observed offsets',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-ball-projection-y.json',import.meta.url),'utf8'));
 assert.equal(report.total_frames,40);assert.equal(report.matched_frames,20);
 for(const frame of report.samples){
  const candidates=frame.candidates.filter(candidate=>candidate.lag===2);
  assert.equal(candidates.length,1);
  const sample=candidates[0],base=project({x:sample.object_x,y:sample.object_y,height:sample.object_height});
  assert.equal(sample.base_x8,base.x8);assert.equal(sample.base_y8,base.y8);
  assert.equal(sample.delta_x,0);assert.equal(sample.delta_y,-3);
 }
 assert.deepEqual(report.candidate_delta_y_by_lag['2'],{'-3':20});
});

import {nativeOamProjectionPart as part} from './native_oam_projection.mjs';
test('non-mirrored part offsets are added in native word arithmetic',()=>{
 assert.deepEqual(part({x:128,y:90,height:0xffd9,partX:0,partY:0xfffd,size:8}),{x:124,y:44});
 assert.deepEqual(part({x:128,y:90,height:0xffd9,partX:4,partY:1,size:16}),{x:124,y:44});
 assert.throws(()=>part({x:1,y:1,height:1,partX:0,partY:0,size:32}),RangeError);
});

test('descriptor offsets reconstruct both directional OAM samples',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-directional-projection.json',import.meta.url),'utf8'));
 assert.equal(report.captures.length,2);
 let total=0;
 for(const capture of report.captures){
  assert.equal(capture.controllers,'both');
  for(const frame of capture.samples){
   const [sample]=frame.candidates.filter(c=>c.lag===2);
   assert.ok(sample);assert.equal(sample.offset_x,0);assert.equal(sample.offset_y,0xfffd);
   const projected=part({x:sample.object_x,y:sample.object_y,height:sample.object_height,partX:sample.offset_x,partY:sample.offset_y,size:8});
   assert.equal(projected.x&255,sample.oam_x);assert.equal(projected.y&255,sample.oam_y);total++;
  }
 }
 assert.equal(total,57);
});
