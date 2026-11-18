import test from 'node:test';
import assert from 'node:assert/strict';
import { nativePenaltyDirection as decode } from './native_penalty_direction.mjs';

test('native direction code table, default and flag', () => {
  for (const [code, base] of [[1, 0], [9, 1], [8, 2], [10, 3], [2, 4]]) {
    assert.deepEqual(decode(code << 8), { code, base, flagSet: false });
    assert.equal(decode((code << 8) | 0x80).flagSet, true);
  }
  assert.deepEqual(decode(0x0300), { code: 3, base: 2, flagSet: false });
  assert.throws(() => decode(-1), RangeError);
});
