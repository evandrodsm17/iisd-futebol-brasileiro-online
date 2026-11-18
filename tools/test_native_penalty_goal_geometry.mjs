import test from 'node:test';
import assert from 'node:assert/strict';
import { nativePenaltyGoalGeometry as goal } from './native_penalty_goal_geometry.mjs';

test('native geometry boundaries and unresolved inputs', () => {
  const shot = { x: 0x18, y: 0x5b, height: 0xffb8 };
  assert.equal(goal(shot), true);
  assert.equal(goal({ ...shot, x: 0x17 }), false);
  assert.equal(goal({ ...shot, x: 0xdf }), true);
  assert.equal(goal({ ...shot, x: 0xe0 }), false);
  assert.equal(goal({ ...shot, y: 0x5c }), null);
  assert.equal(goal({ ...shot, height: 0xffb7 }), false);
  assert.equal(goal({ ...shot, height: 0x7fff }), true);
  assert.equal(goal({ ...shot, flags: 0x0800 }), null);
  assert.throws(() => goal({ ...shot, height: -1 }), RangeError);
});
