import test from 'node:test';
import assert from 'node:assert/strict';
import {nativePenaltyKeeperJump} from './penalty-keeper-jump.mjs';

test('linked and keeper flags gate the observed jump impulse',()=>{
 const base={stateFlags:8,linkedFlags:26,storedJump:0xfffe00,vz:0};
 assert.deepEqual(nativePenaltyKeeperJump(base),{vz:0,storedJump:0xfffe00,nextState:'waiting',applied:false});
 assert.deepEqual(nativePenaltyKeeperJump({...base,linkedFlags:0x2012}),{vz:0xfffe00,storedJump:0xff0000,nextState:'movement',applied:true});
 assert.deepEqual(nativePenaltyKeeperJump({...base,stateFlags:0,linkedFlags:0}),{vz:0,storedJump:0xfffe00,nextState:'movement',applied:false});
 assert.equal(nativePenaltyKeeperJump({...base,linkedFlags:0,storedJump:0xfffd00}).vz,0xfffd00);
 assert.throws(()=>nativePenaltyKeeperJump({...base,storedJump:-1}),RangeError);
});
