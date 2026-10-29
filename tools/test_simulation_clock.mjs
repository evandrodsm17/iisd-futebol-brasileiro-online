import assert from 'node:assert/strict';
import { createSimulationClock } from '../dist/simulation-clock.mjs';
function simulate(hz) {
  let x=0, velocity=0, ticks=0;
  const clock=createSimulationClock(dt=>{
    ticks++;
    velocity+=(2-velocity)*dt*6;
    x+=velocity*dt*60;
  });
  for(let i=0;i<hz*10;i++) clock.advance(1/hz);
  return {x,velocity,ticks};
}
const reference=simulate(60);
assert.equal(reference.ticks,600);
for(const hz of [30,120,144]) assert.deepEqual(simulate(hz),reference);
let ticks=0;
const clock=createSimulationClock(()=>ticks++);
assert.equal(clock.advance(30),6);
clock.advance(1/120);
clock.reset();
assert.equal(clock.advance(1/120),0);
assert.equal(clock.advance(NaN),0);
assert.equal(clock.advance(-1),0);
console.log('Simulation clock: cadence invariance, stall cap and reset passed');
