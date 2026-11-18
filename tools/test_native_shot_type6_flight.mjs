import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {advanceNativeAirborneHeight} from '../dist/native-ball-fixed.mjs';
import {advanceShotAirborne} from '../dist/shot-model.mjs';

const words=n=>({integer:Math.floor(n/65536),fraction:n%65536});
const signed=n=>(n>=0x80000000?n-0x100000000:n)/65536;

test('native and web airborne update order match the recorded type-6 flight',()=>{
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-type6-flight.json','utf8'));
  assert.equal(cases.length,3);
  let count=0;
  for(const c of cases) for(const sample of c.steps){
    assert.deepEqual(advanceNativeAirborneHeight(words(sample.position_before),words(sample.velocity_before),sample.gravity),
      {position:words(sample.position_after),velocity:words(sample.velocity_after)});
    assert.deepEqual(advanceShotAirborne({z:signed(sample.position_before),vz:signed(sample.velocity_before),gravity:sample.gravity/65536}),
      {z:signed(sample.position_after),vz:signed(sample.velocity_after)});
    count++;
  }
  assert.equal(count,198);
});
