import assert from 'node:assert/strict';
import {createGamepadSampler} from '../dist/native-gamepad.mjs';
import {createSubstitutionFlow} from '../dist/native-substitution.mjs';
const pad=(buttons=[],axes=[0,0])=>({index:0,connected:true,mapping:'standard',buttons:Array.from({length:17},(_,i)=>({pressed:buttons.includes(i)})),axes});
const s=createGamepadSampler();
assert.deepEqual(s.sample([pad([2])]).pressed,[]);
s.sample([pad()]);assert.deepEqual(s.sample([pad([2])]).pressed,['shot']);
assert.deepEqual(s.sample([pad([2])]).pressed,[]);
assert.equal(s.sample([pad([],[0.9,0])]).held.has('right'),true);
s.sample([]);assert.deepEqual(s.sample([pad([0])]).pressed,[]);
const m=createSubstitutionFlow();
assert.equal(m.request(),true);assert.equal(m.cancelRequest(),true);
for(const [out,incoming] of [[1,12],[3,14],[5,17]]){
 m.request();m.admitAtStoppage();m.openSquad();
 assert.equal(m.choose(out,{isStarter:true}).committed,false);
 assert.deepEqual(m.choose(incoming,{isStarter:false}).change,{out,in:incoming});
 m.resume();
}
m.request();m.admitAtStoppage();m.openSquad();
assert.equal(m.choose(6,{isStarter:true}).reason,'limit');
assert.equal(m.snapshot().completed,3);
console.log('Native input/menu foundation: OK');
