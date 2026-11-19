import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {projectPenaltyAfterFreeFlight} from './penalty-motion-projection.mjs';
const data=JSON.parse(readFileSync(new URL('./data/issd-penalty-motion-projection.json',import.meta.url),'utf8'));
test('native motion and projection reproduce 74 captured ball positions',()=>{
 let count=0,excluded=0;
 for(const capture of data.captures){excluded+=capture.excluded.length;for(const sample of capture.samples)if(sample){
  const {before,partX,partY,size,oamX,oamY}=sample;
  assert.deepEqual(projectPenaltyAfterFreeFlight(before,data.gravity,{partX,partY,size}).oam,{x:oamX,y:oamY});count++;
 }}
 assert.equal(count,74);assert.equal(excluded,4);
});
test('invalid native state is rejected',()=>assert.throws(()=>projectPenaltyAfterFreeFlight({x:-1},32,{partX:0,partY:0,size:8}),RangeError));
