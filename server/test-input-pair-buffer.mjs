import test from 'node:test';
import assert from 'node:assert/strict';
import {createInputPairBuffer} from './input-pair-buffer.mjs';
const input=(tick,held=0,actions=[])=>({tick,held,actions});
test('pairs in tick and seat order, limits ahead and rejects duplicates',()=>{
 const buffer=createInputPairBuffer(2);
 assert.deepEqual(buffer.submit(2,input(0,2)),{pair:null});
 assert.deepEqual(buffer.submit(2,input(1,4)),{pair:null});
 assert.equal(buffer.submit(2,input(2)).error,'input_window_full');
 assert.equal(buffer.submit(2,input(1)).error,'unexpected_tick');
 assert.deepEqual(buffer.submit(1,input(0,1,['pass'])),{pair:{tick:0,inputs:[input(0,1,['pass']),input(0,2)]}});
 assert.deepEqual(buffer.submit(1,input(1,8)),{pair:{tick:1,inputs:[input(1,8),input(1,4)]}});
 assert.equal(buffer.submit(3,input(2)).error,'invalid_seat');
 assert.equal(buffer.submit(1,input(2,32)).error,'invalid_input');
});
test('copies input data and a new buffer discards unmatched frames',()=>{
 const buffer=createInputPairBuffer(),packet=input(0,0,['shot']);
 buffer.submit(1,packet);packet.actions.push('pass');
 assert.deepEqual(buffer.submit(2,input(0)).pair.inputs[0].actions,['shot']);
 buffer.submit(1,input(1));const next=createInputPairBuffer();
 assert.equal(next.submit(1,input(1)).error,'unexpected_tick');
 assert.deepEqual(next.submit(2,input(0)),{pair:null});
});
