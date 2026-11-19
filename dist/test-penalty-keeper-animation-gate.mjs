import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeLateralKeeperAnimationGate as gate} from './penalty-keeper-animation-gate.mjs';
test('known timer branches follow native word and zero-flag behavior',()=>{
 assert.deepEqual(gate({counter:3,scriptPointer:0x6dde}),{counter:2,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0x6dde}),{counter:0,completed:true,nextState:0x91ac});
 assert.deepEqual(gate({counter:0,scriptPointer:0x6dde}),{counter:65535,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0xedde}),{counter:0,completed:null,nextState:null});
 assert.throws(()=>gate({counter:-1,scriptPointer:0}),RangeError);
});
