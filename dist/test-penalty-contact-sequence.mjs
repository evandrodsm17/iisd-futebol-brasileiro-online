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
