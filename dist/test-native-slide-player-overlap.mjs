import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeSlidePlayerOverlap as overlap} from './native-slide-player-overlap.mjs';
const evidence=JSON.parse(readFileSync(new URL('../docs/issd-slide-player-contact.json',import.meta.url),'utf8'));
const entry=evidence.event_sequence.find(e=>e.site==='player_overlap_entry'),exit=evidence.event_sequence.find(e=>e.site==='player_overlap_return');
const input={actorAddress:entry.actor,linkA6:entry.link_a6,linkA4:0,actorFlags:entry.flags,actor:{x:entry.actor_xy[0],y:entry.actor_xy[1],offsetX:entry.offset_xy[0],offsetY:entry.offset_xy[1]},target:{x:entry.target_xy[0],y:entry.target_xy[1],flags:entry.target_flags}};
const observed=overlap(input);assert.equal(observed.carry,exit.p&1);assert.equal(observed.actorFlags,exit.flags);assert.equal(observed.targetAddress,exit.x);
for(const [axis,offset,low,high] of [['x','offsetX',-17,18],['y','offsetY',-11,12]]){
 const centered={...input,actor:{x:100,y:100,offsetX:0,offsetY:0},target:{x:100,y:100,flags:0}};
 for(const [delta,inside] of [[low-1,false],[low,true],[high,true],[high+1,false]]){
  const trial={...centered,target:{...centered.target,[axis]:(100+delta)&0xffff}};assert.equal(overlap(trial).carry,inside?0:1,`${axis} ${delta}`);
 }
}
assert.equal(overlap({...input,linkA6:0,linkA4:0}).reason,'target');
assert.equal(overlap({...input,linkA6:input.actorAddress}).reason,'target');
assert.equal(overlap({...input,target:{...input.target,flags:0x100}}).reason,'target_flags');
assert.equal(overlap({...input,linkA6:0,linkA4:input.linkA6}).targetAddress,input.linkA6);
assert.throws(()=>overlap({...input,actor:{...input.actor,x:-1}}));
console.log('OK: native player overlap matches captured event, boundaries and gates');

