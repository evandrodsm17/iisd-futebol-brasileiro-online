import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {replayPenaltyKeeper,replayPenaltyKeeperWithGate} from './penalty-keeper-replay.mjs';
const data=JSON.parse(readFileSync(new URL('./data/issd-penalty-keeper-motion.json',import.meta.url),'utf8'));
const schedules={left:9799,neutral:9795,right:9799};
test('continuous keeper replays match all instrumented states with observed impulses',()=>{
 let count=0;
 for(const capture of data.captures){
  const impulse={frame:schedules[capture.direction],vz:capture.stored_jump};
  assert.deepEqual(capture.observed_impulses,[impulse]);
  const frames=replayPenaltyKeeper(capture,[impulse]);
  assert.deepEqual(replayPenaltyKeeperWithGate(capture),frames);
  count+=frames.length;
  assert.equal(frames.find(f=>f.frame===impulse.frame).before.vz,impulse.vz);
  assert.throws(()=>replayPenaltyKeeper(capture,[]),RangeError);
  assert.throws(()=>replayPenaltyKeeper(capture,[{...impulse,frame:impulse.frame+1}]),RangeError);
 }
 assert.equal(count,107);
});
test('the gate rejects a changed linked flag at the recorded transition',()=>{
 const capture=structuredClone(data.captures[0]);
 capture.samples.find(s=>s.frame===9799).linked_flags|=8;
 assert.throws(()=>replayPenaltyKeeperWithGate(capture),RangeError);
});
test('unobserved frames and duplicate impulses are rejected',()=>{
 const capture=structuredClone(data.captures[0]);capture.samples.splice(3,1);
 assert.throws(()=>replayPenaltyKeeper(capture,[{frame:9799,vz:capture.stored_jump}]),RangeError);
 const original=data.captures[0];const impulse={frame:9799,vz:original.stored_jump};
 assert.throws(()=>replayPenaltyKeeper(original,[impulse,impulse]),RangeError);
});
