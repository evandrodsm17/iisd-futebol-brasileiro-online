import test from 'node:test';
import assert from 'node:assert/strict';
import {observedThrowInAirborneHeight,observedThrowInImpact} from './native-throwin-flight.mjs';

test('reconstructs a captured flight tick in 16.16 native units',()=>{
 assert.deepEqual(observedThrowInAirborneHeight(20,{integer:65507,fraction:24576},{integer:65533,fraction:24576}),{position:{integer:65504,fraction:57344},velocity:{integer:65533,fraction:32768}});
 assert.equal(observedThrowInAirborneHeight(3,{integer:65507,fraction:24576},{integer:65533,fraction:24576}),null);
});
test('matches two observed impact snapshots without extrapolation',()=>{
 assert.deepEqual(observedThrowInImpact(20,{integer:65535,fraction:32768},{integer:3,fraction:40960}),{position:{integer:0,fraction:0},velocity:{integer:65534,fraction:8192}});
 assert.deepEqual(observedThrowInImpact(15,{integer:0,fraction:16384},{integer:2,fraction:57344}),{position:{integer:0,fraction:0},velocity:{integer:65534,fraction:32768}});
 assert.equal(observedThrowInImpact(15,{integer:0,fraction:16383},{integer:2,fraction:57344}),null);
});
