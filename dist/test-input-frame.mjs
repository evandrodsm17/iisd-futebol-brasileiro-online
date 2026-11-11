import test from 'node:test';
import assert from 'node:assert/strict';
import {captureInputFrame} from './input-frame.mjs';
import {createActionQueue} from './simulation-input.mjs';
const bindings={up:'KeyW',down:'KeyS',left:'KeyA',right:'KeyD',run:'ShiftLeft'};
test('captures held movement and consumes action edges once in order',()=>{
 const keys=new Set(['KeyW','KeyD','ShiftLeft']),queue=createActionQueue();
 queue.push('pass');queue.push('shot');queue.push('shot',true);
 assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:true,down:false,left:false,right:true,run:true,actions:['pass','shot']});
 assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:true,down:false,left:false,right:true,run:true,actions:[]});
 keys.clear();assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:false,down:false,left:false,right:false,run:false,actions:[]});
});
