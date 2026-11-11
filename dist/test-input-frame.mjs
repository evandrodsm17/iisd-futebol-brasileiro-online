import test from 'node:test';
import assert from 'node:assert/strict';
import {captureInputFrame,inputAxes} from './input-frame.mjs';
import {createActionQueue} from './simulation-input.mjs';
const bindings={up:'KeyW',down:'KeyS',left:'KeyA',right:'KeyD',run:'ShiftLeft'};
test('captures held movement and consumes action edges once in order',()=>{
 const keys=new Set(['KeyW','KeyD','ShiftLeft']),queue=createActionQueue();
 queue.push('pass');queue.push('shot');queue.push('shot',true);
 assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:true,down:false,left:false,right:true,run:true,actions:['pass','shot']});
 assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:true,down:false,left:false,right:true,run:true,actions:[]});
 keys.clear();assert.deepEqual(captureInputFrame(keys,bindings,queue),{up:false,down:false,left:false,right:false,run:false,actions:[]});
});

test('logical axes preserve diagonal direction and cancel opposing inputs',()=>{
 assert.deepEqual(inputAxes({up:true,down:false,left:true,right:false}),{x:-1,y:-1});
 assert.deepEqual(inputAxes({up:true,down:true,left:true,right:true}),{x:0,y:0});
 assert.deepEqual(inputAxes({up:false,down:true,left:false,right:true}),{x:1,y:1});
});
