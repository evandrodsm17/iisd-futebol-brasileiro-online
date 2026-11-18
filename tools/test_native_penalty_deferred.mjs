import test from 'node:test';
import assert from 'node:assert/strict';
import { nativePenaltyDeferredStep as step } from './native_penalty_deferred.mjs';

test('deferred path timer and stop conditions', () => {
  const state = { x: 20, y: 30, height: 1, timer: 0, field28: 0, field29: 0, field32: 0, field33: 0 };
  assert.deepEqual(step(state), { timer: 0, finalize: false, reason: null });
  assert.deepEqual(step({ ...state, x: 0x100 }), { timer: 0xffff, finalize: true, reason: 'timer' });
  assert.deepEqual(step({ ...state, y: 0xff00, timer: 2 }), { timer: 1, finalize: false, reason: null });
  assert.deepEqual(step({ ...state, height: 0 }), { timer: 0, finalize: true, reason: 'fields_zero' });
  assert.deepEqual(step({ ...state, height: 0, field32: 1 }), { timer: 0, finalize: false, reason: null });
  assert.throws(() => step({ ...state, timer: -1 }), RangeError);
});
