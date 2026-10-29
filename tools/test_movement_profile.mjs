import assert from 'node:assert/strict';
import { approachMovement, movementProfiles } from '../dist/movement-profile.mjs';
import { moveFixed } from '../dist/fixed-motion.mjs';
for (const running of [false, true]) {
  const human={x:0,y:0,vx:0,vy:0}, ai={...human};
  for(let tick=0;tick<600;tick++) {
    approachMovement(human,1,1,running,1/60);
    approachMovement(ai,500,500,running,1/60);
    for(const actor of [human,ai]) moveFixed(actor,actor.vx,actor.vy);
    assert.ok(Math.abs(human.vx-ai.vx)<1e-12);
    assert.equal(human.x,ai.x);
    assert.equal(human.y,ai.y);
    assert.ok(Math.hypot(ai.vx,ai.vy)<=movementProfiles[running?'running':'walking'].speed+1e-12);
  }
}
const idle={vx:0,vy:0};
approachMovement(idle,0,0,false,1/60);
assert.deepEqual(idle,{vx:0,vy:0});
console.log('Movement profiles: equal acceleration, speed and displacement for human/AI passed');
