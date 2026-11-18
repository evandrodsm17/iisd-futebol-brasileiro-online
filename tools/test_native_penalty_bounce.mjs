import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nativePenaltyBounce } from './native_penalty_bounce.mjs';

test('penalty bounce clamps height and halves the gravity-adjusted velocity', () => {
  assert.deepEqual(nativePenaltyBounce(65113, 759), { position: 80, velocity: 65141 });
  assert.throws(() => nativePenaltyBounce(-1, 1), RangeError);
});

test('model matches all recorded bounce-pattern samples', () => {
  const { bounce_pattern: samples, stop_pattern: stops } = JSON.parse(readFileSync('docs/issd-penalty-shot-vector.json', 'utf8'));
  assert.equal(samples.length, 19);
  assert.equal(stops.length, 7);
  for (const sample of samples) assert.deepEqual(nativePenaltyBounce(sample.position, sample.velocity),
    { position: sample.next_position, velocity: sample.next_velocity });
});
