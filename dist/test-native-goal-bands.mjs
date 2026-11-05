import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import {nativeDimensions} from './native-field.mjs';
import {nativeGoalBands, nativeGoalBandBranch, nativeGoalEntryBranch, nativeGoalLineCarry} from './native-goal-bands.mjs';

for (let stadium = 0; stadium < nativeDimensions.length; stadium++) {
  const b = nativeGoalBands(stadium), center = nativeDimensions[stadium][1] / 2;
  assert.deepEqual(Object.values(b), [center-56, center-48, center+48, center+56]);
  for (const [value, branch] of [[b.outerLow-1,'outer'], [b.outerLow,'edge'],
    [b.innerLow-1,'edge'], [b.innerLow,'inner'], [b.innerHigh-1,'inner'],
    [b.innerHigh,'edge'], [b.outerHigh-1,'edge'], [b.outerHigh,'outer']]) {
    assert.equal(nativeGoalBandBranch(stadium, value), branch);
  }
}
assert.throws(() => nativeGoalBands(8), RangeError);
assert.throws(() => nativeGoalBandBranch(0, -1), RangeError);

const width = 0x740;
for (const [x, height, expected] of [
  [0xffc0, 0, 'outside'], [0xffc1, 0, 'continue'],
  [width+0x47, 0, 'continue'], [width+0x48, 0, 'outside'],
  [0, 0xffbf, 'outside'], [0, 0xffc0, 'height-response'],
  [0, 0xffc7, 'height-response'], [0, 0xffc8, 'continue'],
  [0, 0xffff, 'continue'], [0, 0, 'continue'],
]) assert.equal(nativeGoalEntryBranch(x, height, width), expected);
for (const [x, carry] of [[0xfffa,false], [0xfffb,false], [0xfffc,true],
  [0xffff,true], [0,true], [width+3,true], [width+4,false]]) {
  assert.equal(nativeGoalLineCarry(x, width), carry);
}
assert.throws(() => nativeGoalEntryBranch(0, -1, width), RangeError);

// Optional local verification; the ROM itself must never be distributed.
const romPath = new URL('../International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc', import.meta.url);
if (existsSync(romPath)) {
  const rom = readFileSync(romPath);
  for (let stadium = 0; stadium < 8; stadium++) {
    const expected = Object.values(nativeGoalBands(stadium));
    for (let i = 0; i < 4; i++) assert.equal(rom.readUInt16LE(0xa833 + i * 16 + stadium * 2), expected[i]);
  }
  console.log('OK: 32 thresholds match the local USA ROM');
} else console.log('ROM unavailable: local ROM comparison skipped');
console.log('OK: goal-band branches and boundary inclusivity');
