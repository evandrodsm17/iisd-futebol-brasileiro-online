import test from 'node:test';
import assert from 'node:assert/strict';
import {selectNativePenaltyContact as select,applySelectedNativePenaltyContact as apply} from './penalty-contact-sequence.mjs';
const tables={schema:'issd-penalty-hitbox-tables/v1',tables:[{selector:0,rectangles:[[0,251,5,5]]}]};
const geometry={x:100,y:100,z:100,otherX:102,otherY:100,otherZ:100,objectFlags:0,offset:0};
const response={target:{y:0x123456,vx:1,vy:2,vz:3},peerY:100,source:{vx:4,vz:0}};

test('blocked, missed and gated hits cannot schedule a reaction',()=>{
 assert.deepEqual(select({flags:0x20,shotIndex:0,tick:1}),{disposition:'blocked',hit:null,selection:null});
 assert.equal(select({tables,selector:0,geometry:{...geometry,otherX:110},flags:0,shotIndex:0,tick:1}).disposition,'miss');
 assert.equal(select({tables,selector:0,geometry,flags:0x100,shotIndex:5,tick:1}).disposition,'excluded');
});

test('a selected contact acts only later and does not mutate its inputs',()=>{
 const found=select({tables,selector:0,geometry,flags:0x100,shotIndex:2,tick:10});
 assert.equal(found.disposition,'selected');assert.equal(found.hit,true);
 assert.throws(()=>apply(found.selection,{tick:10,flags:0,...response}),RangeError);
 const applied=apply(found.selection,{tick:11,flags:0x100,...response});
 assert.equal(applied.phase,'applied');assert.equal(applied.flags,0x800);assert.equal(applied.target.y,0x6856);
 assert.equal(found.selection.phase,'pending');assert.equal(response.target.vy,2);
 assert.throws(()=>apply(applied,{tick:12,flags:0,...response}),RangeError);
 const cancelled=apply(found.selection,{tick:11,flags:0x20,...response});
 assert.equal(cancelled.phase,'cancelled');assert.equal(cancelled.target,null);assert.equal(cancelled.flags,0x20);
 const flag40=apply(found.selection,{tick:11,flags:0x40,...response});assert.equal(flag40.phase,'applied');assert.equal(flag40.flags,0x840);
});

import {existsSync,readFileSync} from 'node:fs';
const localTables='dist/assets/issd/penalty-hitbox-tables-local.json';
test('the two captured contacts follow hit, delayed action and response', {skip:!existsSync(localTables)},()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-contact-chain.json',import.meta.url),'utf8'));
 const actualTables=JSON.parse(readFileSync(localTables,'utf8'));
 assert.equal(report.cases.length,2);
 for(const sample of report.cases){
  const found=select({tables:actualTables,selector:sample.selector,geometry:sample.geometry,flags:sample.selection_flags,shotIndex:sample.shot_index,tick:sample.selected_frame});
  assert.equal(found.disposition,'selected');
  const input=sample.response_input;
  const action=apply(found.selection,{tick:sample.action_frame,flags:sample.action_flags,
   target:{y:input.target_y,vx:input.target_vx,vy:input.target_vy,vz:input.target_vz},
   peerY:input.peer_y,source:{vx:input.source_vx,vz:input.source_vz}});
  assert.equal(action.flags,sample.result_flags);
  const output=sample.response_output;
  assert.deepEqual(action.target,{y:output.target_y,vx:output.target_vx,vy:output.target_vy,vz:output.target_vz});
 }
});

import {advanceSelectedPenaltyDeferred as advance} from './penalty-contact-sequence.mjs';
test('deferred step waits for a native stop or timer and clears only the deferred flag',()=>{
 const selected=select({tables,selector:0,geometry,flags:0,shotIndex:0,tick:10}).selection;
 const applied=apply(selected,{tick:11,flags:0,...response});
 const snapshot={x:10,y:20,height:1,timer:2,field28:1,field29:0,field32:0,field33:0};
 assert.throws(()=>advance(applied,{tick:11,flags:0x800,snapshot}),RangeError);
 const pending=advance(applied,{tick:12,flags:0x800,snapshot});
 assert.equal(pending.phase,'applied');assert.equal(pending.timer,2);assert.equal(pending.flags,0x800);
 assert.throws(()=>advance(pending,{tick:13,flags:0x800,snapshot:{...snapshot,timer:1}}),RangeError);
 const done=advance(pending,{tick:13,flags:0x841,snapshot:{...snapshot,height:0,field28:0}});
 assert.equal(done.phase,'resolved');assert.equal(done.reason,'fields_zero');assert.equal(done.flags,0x41);
 assert.throws(()=>advance(done,{tick:14,flags:0,snapshot}),RangeError);
 const timed=advance(applied,{tick:12,flags:0x800,snapshot:{...snapshot,x:0x100,timer:0}});
 assert.equal(timed.phase,'resolved');assert.equal(timed.timer,0xffff);assert.equal(timed.reason,'timer');
});

test('captured contacts remain pending through 78 checks until native timer resolves', {skip:!existsSync(localTables)},()=>{
 const chain=JSON.parse(readFileSync(new URL('../docs/issd-penalty-contact-chain.json',import.meta.url),'utf8'));
 const deferred=JSON.parse(readFileSync(new URL('../docs/issd-penalty-deferred-checks.json',import.meta.url),'utf8'));
 const actualTables=JSON.parse(readFileSync(localTables,'utf8'));
 assert.equal(deferred.cases.length,2);
 for(let i=0;i<2;i++){
  const c=chain.cases[i],d=deferred.cases[i];
  let state=select({tables:actualTables,selector:c.selector,geometry:c.geometry,flags:c.selection_flags,shotIndex:c.shot_index,tick:c.selected_frame}).selection;
  const a=c.response_input;
  state=apply(state,{tick:c.action_frame,flags:c.action_flags,target:{y:a.target_y,vx:a.target_vx,vy:a.target_vy,vz:a.target_vz},peerY:a.peer_y,source:{vx:a.source_vx,vz:a.source_vz}});
  assert.equal(d.checks.length,39);
  for(const check of d.checks){
   state=advance(state,{tick:check.frame,flags:check.flags,snapshot:check.snapshot});
   assert.equal(state.timer,check.result_timer);assert.equal(state.reason,check.reason);
   assert.equal(state.phase,check.finalize?'resolved':'applied');
  }
  assert.equal(state.checkedAt,d.resolved_frame);assert.equal(state.flags,d.resolved_flags);assert.equal(state.reason,'timer');
 }
});

test('captured stopped-field resolutions clear the deferred flag without inventing a score',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-deferred.json',import.meta.url),'utf8'));
 assert.equal(report.cases.length,3);
 for(const sample of report.cases){
  const e=sample.finalize;
  const state={phase:'applied',actionAt:e.frame-1,selectedAt:e.frame-2,selector:0};
  const result=advance(state,{tick:e.frame,flags:e.shot_flags,snapshot:{x:e.x_coord,y:e.y_coord,height:e.height,timer:e.field_24,field28:e.field_28,field29:e.field_29,field32:e.field_32,field33:e.field_33}});
  assert.equal(result.phase,'resolved');assert.equal(result.reason,'fields_zero');assert.equal(result.flags,sample.resolved.shot_flags);
  assert.equal(Object.hasOwn(result,'scored'),false);
 }
});
