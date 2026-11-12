import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeSlideReactionChoice as choose,nativeSlideReactionTable as table,nativeIdleGlobal78 as idle,resolveNativeSlideReaction as resolve,candidateSlideReactionRecord as recordFromCatalog,unpackNativeReactionFieldGroup as unpack} from './native-slide-reaction-choice.mjs';
assert.deepEqual(unpack(0),[0,0,0,0,0]);
assert.deepEqual(unpack(0x7fff),[7,7,7,7,7]);
assert.deepEqual(unpack(0xd1a1),[1,4,6,0,5]);
assert.throws(()=>unpack(65536),RangeError);
const base={attackerAddress:0x0d00,attacker60:0x4000,targetAddress:0x1900,target30:2,target60:0,target68:1,target6c:0,target6e:0,foulSetting:1,global11f9:0,tableByte:1};
assert.deepEqual(choose(base),{route:'selected',carry:0,target6e:0x200,reaction:4,source:0x0d00,globalC6:0x1900});
assert.equal(choose({...base,target30:1}).reaction,0);
for(const change of [{global11f9:0x8000},{tableByte:0},{tableByte:2},{target60:0x800}]){
 const result=choose({...base,...change});assert.equal(result.route,'fallback');assert.equal(result.reaction,0x2002);assert.equal(result.carry,1);
}
assert.deepEqual(choose({...base,target68:0,target6c:0,global11f9:0x8000}),{route:'early_return',carry:0,target6e:0});
assert.equal(choose({...base,target68:0,target6c:0x100,global11f9:0x8000}).route,'fallback');
assert.equal(choose({...base,target68:0,foulSetting:0,global11f9:0x8000}).route,'fallback');
assert.equal(choose({...base,attacker60:0}).route,'early_return');
assert.equal(choose({...base,target6e:0x400}).target6e,0x600);
assert.throws(()=>choose({...base,tableByte:256}),RangeError);
assert.deepEqual(table({attacker30:1,recordWord:0,recordNextWord:0,recordSixthWord:0,global78:0}),{route:'table',index:0,tableByte:0});
assert.deepEqual(table({attacker30:4,recordWord:0x40,recordNextWord:0x40,recordSixthWord:0,global78:3}),{route:'table',index:23,tableByte:1});
assert.deepEqual(table({attacker30:6,recordWord:0x40,recordNextWord:0x20,recordSixthWord:1,global78:3}),{route:'table',index:27,tableByte:1});
assert.equal(table({attacker30:0,recordWord:0,recordNextWord:0,recordSixthWord:0,global78:0}).route,'unresolved_attacker_class');
assert.equal(table({attacker30:6,recordWord:0xf0,recordNextWord:0xf0,recordSixthWord:15,global78:3}).route,'unresolved_table_index');
assert.throws(()=>table({attacker30:1,recordWord:-1,recordNextWord:0,recordSixthWord:0,global78:0}),RangeError);
const replay=JSON.parse(readFileSync(new URL('../docs/issd-slide-reaction-choice-observation.json',import.meta.url),'utf8'));
const e=replay.entry,r=replay.record;
const catalog=JSON.parse(readFileSync(new URL('./data/issd-rom-catalog.json',import.meta.url),'utf8'));
const candidates=catalog.teams.flatMap(team=>team.players.map(player=>({team,player}))).filter(({player})=>{
 const candidate=recordFromCatalog(player.raw.attributes_hex,r.record_sixth_word);
 return candidate.recordWord===r.record_word&&candidate.recordNextWord===r.record_next_word;
});
assert.equal(candidates.length,1,'catalog has one matching raw byte sequence');
assert.equal(candidates[0].team.name,'England');assert.equal(candidates[0].player.name,'T.Keegan');
assert.deepEqual(recordFromCatalog(candidates[0].player.raw.attributes_hex,r.record_sixth_word),{recordWord:r.record_word,recordNextWord:r.record_next_word,recordSixthWord:r.record_sixth_word});
assert.throws(()=>recordFromCatalog('not-hex',0),RangeError);assert.throws(()=>recordFromCatalog(candidates[0].player.raw.attributes_hex,-1),RangeError);
const observed=table({attacker30:e.attacker30,recordWord:r.record_word,recordNextWord:r.record_next_word,recordSixthWord:r.record_sixth_word,global78:e.global78});
assert.equal(observed.index,replay.index);assert.equal(observed.tableByte,replay.table_byte);
// target68 is nonzero, so foulSetting cannot affect the early branch in this replay.
for(const foulSetting of [0,1]){
 const reaction=choose({attackerAddress:e.d,attacker60:e.attacker60,targetAddress:e.x,target30:e.target30,target60:e.target60,target68:e.target68,target6c:e.target6c,target6e:e.target6e,foulSetting,global11f9:e.global11f9,tableByte:observed.tableByte});
 assert.equal(reaction.reaction,replay.store.a);assert.equal(reaction.source,replay.dispatch.target76);assert.equal(reaction.target6e,replay.store.target6e);
 const combined=resolve({attackerAddress:e.d,attacker30:e.attacker30,attacker60:e.attacker60,targetAddress:e.x,target30:e.target30,target60:e.target60,target68:e.target68,target6c:e.target6c,target6e:e.target6e,foulSetting,global11f9:e.global11f9,global78:e.global78,recordWord:r.record_word,recordNextWord:r.record_next_word,recordSixthWord:r.record_sixth_word});
 assert.equal(combined.tableIndex,replay.index);assert.equal(combined.tableByte,replay.table_byte);assert.equal(combined.reaction,replay.store.a);
}
const fall=JSON.parse(readFileSync(new URL('../docs/issd-slide-reaction-fall-observation.json',import.meta.url),'utf8'));
const f=fall.entry,fr=fall.record;
assert.deepEqual([r.record_word,r.record_next_word,r.record_sixth_word],[fr.record_word,fr.record_next_word,fr.record_sixth_word]);
const fallTable=table({attacker30:f.attacker30,recordWord:fr.record_word,recordNextWord:fr.record_next_word,recordSixthWord:fr.record_sixth_word,global78:f.global78});
assert.equal(fallTable.index,fall.index);assert.equal(fallTable.tableByte,fall.table_byte);
for(const foulSetting of [0,1]){
 const result=choose({attackerAddress:f.d,attacker60:f.attacker60,targetAddress:f.x,target30:f.target30,target60:f.target60,target68:f.target68,target6c:f.target6c,target6e:f.target6e,foulSetting,global11f9:f.global11f9,tableByte:fallTable.tableByte});
 assert.equal(result.reaction,fall.dispatch.target78);assert.equal(result.source,fall.dispatch.target76);assert.equal(result.target6e,fall.dispatch.target6e);
 const combined=resolve({attackerAddress:f.d,attacker30:f.attacker30,attacker60:f.attacker60,targetAddress:f.x,target30:f.target30,target60:f.target60,target68:f.target68,target6c:f.target6c,target6e:f.target6e,foulSetting,global11f9:f.global11f9,global78:f.global78,recordWord:fr.record_word,recordNextWord:fr.record_next_word,recordSixthWord:fr.record_sixth_word});
 assert.equal(combined.tableIndex,fall.index);assert.equal(combined.tableByte,fall.table_byte);assert.equal(combined.reaction,fall.dispatch.target78);
}
const missingClass={...base,attacker30:0,recordWord:0,recordNextWord:0,recordSixthWord:0,global78:0};
assert.equal(resolve(missingClass).route,'unresolved_attacker_class');
assert.equal(resolve({...missingClass,attacker60:0}).route,'early_return','early exits do not require a table lookup');
const loop=JSON.parse(readFileSync(new URL('../docs/issd-reaction-global78-observation.json',import.meta.url),'utf8'));
for(const run of [loop.jump,loop.fall])for(const pair of [run.example_pair,run.carry_pair]){
 const [before,after]=pair,actual=idle(before.a,after.addend,before.p&1);
 assert.equal(actual.value,after.a);assert.equal(actual.carry,after.p&1);
}
assert.deepEqual(idle(65535,0,1),{value:0,carry:1});
assert.throws(()=>idle(1,1,2),RangeError);
console.log('OK: seleção parcial de reação após contato, baseada no disassembly');
