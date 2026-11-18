import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { nativePenaltyHitbox as hit, readNativePenaltyRectangles } from './native_penalty_hitbox.mjs';

test('contact ranges, mirror and native wrapping', () => {
  const value = { x: 100, y: 100, z: 100, otherX: 102, otherY: 100, otherZ: 100, objectFlags: 0, offset: 0, rectangles: [[0, 251, 5, 5]] };
  assert.equal(hit(value), true);
  assert.equal(hit({ ...value, otherX: 105 }), false);
  assert.equal(hit({ ...value, otherY: 112 }), false);
  assert.equal(hit({ ...value, otherZ: 106 }), false);
  assert.equal(hit({ ...value, objectFlags: 0x10, otherX: 98 }), true);
  assert.equal(hit({ ...value, objectFlags: 0x10, otherX: 102 }), false);
  assert.equal(hit({ ...value, rectangles: [[8, 251, 10, 5], [0, 251, 5, 5]] }), true);
  assert.throws(() => hit({ ...value, rectangles: [[0, 1]] }), RangeError);
});

test('table read preserves bytes beyond an unaligned end', () => {
  const bytes = Uint8Array.from([4, 222, 4, 248, 226, 5, 248, 0]);
  assert.deepEqual(readNativePenaltyRectangles(bytes, 0, 7), [[4, 222, 4, 248], [226, 5, 248, 0]]);
  assert.throws(() => readNativePenaltyRectangles(bytes.subarray(0, 7), 0, 7), RangeError);
});

const romPath = 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc';
const tracePath = 'analysis/movement-progression-probe/world-penalty-hitboxes/mode-hooks.jsonl';
test('captured collision outcomes match original rectangles', { skip: !existsSync(romPath) || !existsSync(tracePath) }, () => {
  const rom = readFileSync(romPath);
  assert.deepEqual(readNativePenaltyRectangles(rom, 0xde87, 0xde8e), [[4, 222, 4, 248], [226, 5, 248, 0]]);
  const events = readFileSync(tracePath, 'utf8').trim().split('\n').map(JSON.parse).filter(e => ['collision_hit', 'collision_miss'].includes(e.site));
  assert.ok(events.some(e => e.site === 'collision_hit'));
  assert.ok(events.some(e => e.site === 'collision_miss'));
  for (const e of events) {
    const end = rom.readUInt16LE(e.table_pointer);
    const rectangles = readNativePenaltyRectangles(rom, e.table_pointer + 2, end);
    const result = hit({ x: e.x, y: e.y, z: e.z, otherX: e.other_x, otherY: e.other_y, otherZ: e.other_z, objectFlags: e.object_flags, offset: e.offset, rectangles });
    assert.equal(result, e.site === 'collision_hit', `frame ${e.frame}`);
  }
});
