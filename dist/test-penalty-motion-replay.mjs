import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {replayCapturedPenaltyMotion} from './penalty-motion-replay.mjs';
const motion=JSON.parse(readFileSync(new URL('./data/issd-penalty-motion-projection.json',import.meta.url),'utf8'));
const exceptions=JSON.parse(readFileSync(new URL('./data/issd-penalty-motion-exceptions.json',import.meta.url),'utf8'));
test('single evolving state follows both 39-frame excerpts through goal and bounce',()=>{
 for(const capture of motion.captures){
  const extra=exceptions.captures.find(item=>item.input===capture.input);const frames=replayCapturedPenaltyMotion(capture,extra,motion.gravity);
  assert.equal(frames.filter(Boolean).length,39);assert.equal(frames[0],null);
  assert.equal(frames.filter(f=>f?.kind==='goal_crossing').length,1);assert.equal(frames.filter(f=>f?.kind==='ground_bounce').length,1);
 }
});
test('replay rejects a broken trajectory or a mismatched recording',()=>{
 const broken=structuredClone(motion.captures[0]);broken.samples[5].before.vx++;
 assert.throws(()=>replayCapturedPenaltyMotion(broken,exceptions.captures[0],motion.gravity),RangeError);
 assert.throws(()=>replayCapturedPenaltyMotion(motion.captures[0],exceptions.captures[1],motion.gravity),RangeError);
});
