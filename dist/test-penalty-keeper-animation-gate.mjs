import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeLateralKeeperAnimationGate as gate,nativePenaltyAnimationReload as reload} from './penalty-keeper-animation-gate.mjs';
test('known timer branches follow native word and zero-flag behavior',()=>{
 assert.deepEqual(gate({counter:3,scriptPointer:0x6dde}),{counter:2,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0x6dde}),{counter:0,completed:true,nextState:0x91ac});
 assert.deepEqual(gate({counter:0,scriptPointer:0x6dde}),{counter:65535,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0xedde}),{counter:0,completed:null,nextState:null});
 assert.throws(()=>gate({counter:-1,scriptPointer:0}),RangeError);
});
test('sequence reload reads duration and descriptors before graphics dispatch',()=>{
 const words=new Map([[0xedde,0x0303],[0xeddf,0x0303],[0xede0,0x0003],[0xede6,0xedf4],[0xedf4,0xee18],[0xedf6,0xee50],[0xedf8,0xee58]]);
 const read=address=>words.get(address);
 let state={scriptPointer:0xedde,index:0,tablePointer:0xede6,variant:0};
 for(const [index,descriptor] of [[2,0xee18],[4,0xee50],[6,0xee58]]){
  const next=reload(state,read);assert.equal(next.counter,3);assert.equal(next.index,index);assert.equal(next.frameDescriptor,descriptor);assert.equal(next.completed,null);
  state={...state,scriptPointer:next.scriptPointer,index:next.index};
 }
 assert.equal(state.scriptPointer,0x6dde);
 assert.deepEqual(gate({counter:1,scriptPointer:state.scriptPointer}),{counter:0,completed:true,nextState:0x91ac});
 assert.throws(()=>reload(state,read),RangeError);
 const endWords=new Map([[0x8000,0x0004],[0xffff,0x0100],[0x0100,0x1234]]);
 assert.deepEqual(reload({scriptPointer:0x8000,index:0,tablePointer:0xffff,variant:0},a=>endWords.get(a)),{counter:4,scriptPointer:0,index:0,frameDescriptor:0x9234,completed:null});
 const example={scriptPointer:0xedde,index:0,tablePointer:0xede6,variant:0};
 assert.equal(reload({...example,savedBank:0x81},read).completed,false);
 assert.equal(reload({...example,savedBank:0},read).completed,true);
 assert.throws(()=>reload({...example,savedBank:256},read),RangeError);
});
