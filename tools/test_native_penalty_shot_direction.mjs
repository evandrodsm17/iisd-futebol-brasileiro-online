import test from 'node:test';
import assert from 'node:assert/strict';
import { nativePenaltyShotDirection as decode } from './native_penalty_shot_direction.mjs';

test('shot index follows the native table and independent flag', () => {
  for (const [code, base] of [[1, 0], [9, 1], [8, 2], [10, 3], [2, 4], [3, 2]]) {
    assert.deepEqual(decode(code << 8, 0x10), { code, base, index: base });
    assert.deepEqual(decode((code << 8) | 0x80, 0), { code, base, index: base + 5 });
  }
  assert.throws(() => decode(-1, 0), RangeError);
  assert.throws(() => decode(0, 0x10000), RangeError);
});
