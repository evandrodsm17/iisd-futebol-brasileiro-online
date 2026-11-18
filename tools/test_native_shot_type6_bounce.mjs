import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {observedType6ShotBounce as bounce} from '../dist/native-ball-fixed.mjs';

test('type-6 first bounce reproduces all three captured states',()=>{
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-type6-bounce.json','utf8'));
  assert.equal(cases.length,3);
  for(const {entry,exit} of cases){
    const input={ballType:entry.ballType,weather:entry.weather,flags:entry.flags,parameter:entry.parameter,
      velocityX:{integer:entry.vx,fraction:entry.vxFrac},velocityY:{integer:entry.vy,fraction:entry.vyFrac},
      impactVelocity:{integer:entry.vz,fraction:entry.vzFrac}};
    assert.deepEqual(bounce(input),{positionZ:{integer:exit.z,fraction:exit.zFrac},
      velocityZ:{integer:exit.vz,fraction:exit.vzFrac},velocityX:{integer:exit.vx,fraction:exit.vxFrac},
      velocityY:{integer:exit.vy,fraction:exit.vyFrac},parameter:exit.parameter,flags:exit.flags});
    assert.equal(bounce({...input,weather:2}),null);
    assert.equal(bounce({...input,velocityX:{integer:entry.vx,fraction:entry.vxFrac+1}}),null);
  }
});
