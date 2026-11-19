import test from 'node:test';
import assert from 'node:assert/strict';
import {createPenaltySession,launchPenaltyShot} from './penalty-session.mjs';
import {resolveNativePenaltyCrossing as resolve} from './penalty-resolution.mjs';

function flight(){return launchPenaltyShot(createPenaltySession(0),{team:0,tick:10,inputWord:0,flags:0});}
const location={x:0x80,y:0x5b,height:0xffd9};
test('native gate waits without changing the score; goal and misses resolve once',()=>{
 const s=flight();
 for(const [flags,position] of [[0,{...location,y:0x5c}],[0x800,location]]){
  const value=resolve(s,{team:0,attempt:0,tick:11,flags,position});
  assert.equal(value.status,'waiting');assert.equal(value.session,s);assert.deepEqual(s.shootout.score,[0,0]);
 }
 const goal=resolve(s,{team:0,attempt:0,tick:11,flags:0,position:location});
 assert.equal(goal.reason,'goal_branch');assert.deepEqual(goal.session.shootout.score,[1,0]);
 assert.throws(()=>resolve(goal.session,{team:0,attempt:0,tick:12,flags:0,position:location}),RangeError);
 for(const position of [{...location,x:0xffff},{...location,height:0xffb7}]){
  const miss=resolve(s,{team:0,attempt:0,tick:11,flags:0,position});
  assert.equal(miss.status,'resolved');assert.deepEqual(miss.session.shootout.score,[0,0]);
 }
});
test('deferred contact cannot resolve a different shot or an unfinished wait',()=>{
 const s=flight(),contact={phase:'applied',selectedAt:11,actionAt:12,flags:0x800};
 assert.equal(resolve(s,{team:0,attempt:0,tick:13,flags:0x800,deferred:contact}).status,'waiting');
 const done={...contact,phase:'resolved',checkedAt:20,flags:0};
 assert.throws(()=>resolve(s,{team:0,attempt:0,tick:19,flags:0,deferred:done}),RangeError);
 assert.throws(()=>resolve(s,{team:0,attempt:0,tick:20,flags:0,deferred:{...done,selectedAt:9}}),RangeError);
 const result=resolve(s,{team:0,attempt:0,tick:20,flags:0,deferred:done});
 assert.equal(result.reason,'deferred');assert.deepEqual(result.session.shootout.score,[0,0]);
});

import {existsSync,readFileSync} from 'node:fs';
import {continuePenaltySession} from './penalty-session.mjs';
import {selectNativePenaltyContact,applySelectedNativePenaltyContact,advanceSelectedPenaltyDeferred} from './penalty-contact-sequence.mjs';
const localTables='dist/assets/issd/penalty-hitbox-tables-local.json';
test('eight captured shots progress through native outcomes and the shootout score', {skip:!existsSync(localTables)},()=>{
 const outcomes=JSON.parse(readFileSync(new URL('../docs/issd-penalty-native-outcomes.json',import.meta.url),'utf8'));
 const contacts=JSON.parse(readFileSync(new URL('../docs/issd-penalty-contact-chain.json',import.meta.url),'utf8'));
 const waits=JSON.parse(readFileSync(new URL('../docs/issd-penalty-deferred-checks.json',import.meta.url),'utf8'));
 const tables=JSON.parse(readFileSync(localTables,'utf8'));
 let session=createPenaltySession(0),deferredCount=0;
 for(const shot of outcomes.cases){
  const team=shot.side/2;
  session=launchPenaltyShot(session,{team,tick:shot.launch_frame,inputWord:shot.input_word,flags:shot.launch_flags});
  let contact;
  if(shot.reason==='deferred'){
   const wait=waits.cases.find(item=>item.resolved_frame===shot.resolved_frame);
   const c=contacts.cases.find(item=>item.action_frame===wait.action_frame);
   contact=selectNativePenaltyContact({tables,selector:c.selector,geometry:c.geometry,flags:c.selection_flags,shotIndex:c.shot_index,tick:c.selected_frame}).selection;
   assert.ok(contact);
   const a=c.response_input;
   contact=applySelectedNativePenaltyContact(contact,{tick:c.action_frame,flags:c.action_flags,target:{y:a.target_y,vx:a.target_vx,vy:a.target_vy,vz:a.target_vz},peerY:a.peer_y,source:{vx:a.source_vx,vz:a.source_vz}});
   assert.deepEqual(session.shootout.score,wait.initial_score);
   for(const check of wait.checks)contact=advanceSelectedPenaltyDeferred(contact,{tick:check.frame,flags:check.flags,snapshot:check.snapshot});
   assert.equal(contact.phase,'resolved');deferredCount++;
  }
  const result=resolve(session,{team,attempt:session.shot.attempt,tick:shot.resolved_frame,flags:shot.resolution_flags,position:shot.position,...(contact?{deferred:contact}:{})});
  assert.equal(result.status,'resolved');assert.equal(result.reason,shot.reason);
  assert.deepEqual(result.session.shootout.score,shot.score);
  session=continuePenaltySession(result.session);
 }
 assert.equal(deferredCount,2);assert.equal(session.phase,'finished');assert.equal(session.shootout.winner,1);
});
