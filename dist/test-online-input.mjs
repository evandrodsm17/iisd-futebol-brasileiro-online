import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeOnlineInput,decodeOnlineInput} from './online-input.mjs';
const frame={up:true,down:false,left:true,right:false,run:true,actions:['pass','shot','pass']};
test('online input preserves held keys, tick and ordered repeated actions',()=>{
 const packet=encodeOnlineInput(42,frame);assert.deepEqual(packet,{tick:42,held:21,actions:['pass','shot','pass']});
 assert.deepEqual(decodeOnlineInput(JSON.parse(JSON.stringify(packet))),{tick:42,frame});
 packet.actions.push('press');assert.equal(frame.actions.length,3);
});
test('rejects malformed or unbounded packets and local reset',()=>{
 for(const packet of [null,[],{}, {tick:-1,held:0,actions:[]},{tick:1.5,held:0,actions:[]},{tick:Number.MAX_SAFE_INTEGER+1,held:0,actions:[]},{tick:0,held:32,actions:[]},{tick:0,held:-1,actions:[]},{tick:0,held:0,actions:['reset']},{tick:0,held:0,actions:Array(33).fill('pass')},{tick:0,held:0,actions:[],extra:true}])assert.equal(decodeOnlineInput(packet),null);
 assert.equal(encodeOnlineInput(0,{...frame,actions:['reset']}),null);
 assert.equal(encodeOnlineInput(0,{...frame,up:1}),null);
});
