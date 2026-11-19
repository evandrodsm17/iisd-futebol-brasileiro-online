import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createPenaltySession,launchPenaltyShot,resolvePenaltyShot,continuePenaltySession} from './penalty-session.mjs';

test('only an explicit resolved shot changes score; duplicate and stale events fail',()=>{
 const initial=createPenaltySession(0);
 assert.throws(()=>resolvePenaltyShot(initial,{team:0,attempt:0,tick:1,scored:true}),RangeError);
 assert.throws(()=>launchPenaltyShot(initial,{team:1,tick:0,inputWord:0,flags:0}),RangeError);
 const flight=launchPenaltyShot(initial,{team:0,tick:10,inputWord:0x100,flags:0x1284});
 assert.equal(flight.phase,'flight');assert.deepEqual(flight.shootout.score,[0,0]);
 assert.deepEqual(flight.shot.direction,{code:1,base:0,index:5});
 assert.throws(()=>launchPenaltyShot(flight,{team:0,tick:11,inputWord:0,flags:0}),RangeError);
 assert.throws(()=>resolvePenaltyShot(flight,{team:1,attempt:0,tick:11,scored:true}),RangeError);
 assert.throws(()=>resolvePenaltyShot(flight,{team:0,attempt:0,tick:9,scored:true}),RangeError);
 assert.throws(()=>resolvePenaltyShot(flight,{team:0,attempt:1,tick:12,scored:true}),RangeError);
 const result=resolvePenaltyShot(flight,{team:0,attempt:0,tick:12,scored:true});
 assert.equal(result.phase,'result');assert.deepEqual(result.shootout.score,[1,0]);
 assert.deepEqual(initial.shootout.score,[0,0]);assert.deepEqual(flight.shootout.score,[0,0]);
 assert.throws(()=>resolvePenaltyShot(result,{team:0,attempt:0,tick:12,scored:true}),RangeError);
 const next=continuePenaltySession(result);assert.equal(next.phase,'aim');assert.equal(next.shootout.nextTeam,1);assert.equal(next.shot,null);
});

test('replay captured native commands and resolved outcomes without predicting saves',()=>{
 const {shots}=JSON.parse(readFileSync(new URL('../docs/issd-penalty-shot-chain.json',import.meta.url),'utf8'));
 let session=createPenaltySession(0);
 for(const shot of shots){
  const team=shot.side/2;
  session=launchPenaltyShot(session,{team,tick:shot.frame,inputWord:shot.input_word,flags:shot.flags});
  assert.equal(session.shot.direction.index,shot.index);
  session=resolvePenaltyShot(session,{team,attempt:session.shot.attempt,tick:shot.resolved_frame,scored:shot.resolution==='goal_branch'});
  assert.deepEqual(session.shootout.score,shot.score);
  session=continuePenaltySession(session);
 }
 assert.equal(session.phase,'finished');assert.equal(session.shootout.winner,1);
 assert.throws(()=>launchPenaltyShot(session,{team:0,tick:99999,inputWord:0,flags:0}),RangeError);
});

test('an old result cannot resolve a later shot by the same team',()=>{
 let session=createPenaltySession(0);
 for(let attempt=0;attempt<2;attempt++){
  const team=session.shootout.nextTeam;
  session=launchPenaltyShot(session,{team,tick:attempt*10,inputWord:0,flags:0});
  session=resolvePenaltyShot(session,{team,attempt,tick:attempt*10+1,scored:false});
  session=continuePenaltySession(session);
 }
 session=launchPenaltyShot(session,{team:0,tick:20,inputWord:0,flags:0});
 assert.throws(()=>resolvePenaltyShot(session,{team:0,attempt:0,tick:21,scored:true}),RangeError);
 assert.deepEqual(session.shootout.score,[0,0]);
});
