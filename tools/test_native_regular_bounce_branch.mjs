import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { nativeRegularVerticalBounce as bounce } from './native_regular_bounce_branch.mjs';

test('vertical branch follows velocity, flag and type table', () => {
  const rom = new Uint8Array(0xa8b3);
  rom[0xa873 + 10] = 1;
  const input = { ballType:5, flags:0, velocity:{integer:2, fraction:4096} };
  assert.deepEqual(bounce(rom,input),{branch:'seven-eighths',velocity:{integer:1,fraction:52736}});
  assert.equal(bounce(rom,{...input,flags:1}).branch,'half');
  assert.equal(bounce(rom,{...input,ballType:3}).branch,'half');
  assert.equal(bounce(rom,{...input,velocity:{integer:4,fraction:0}}).branch,'half');
  assert.equal(bounce(rom,{...input,velocity:{integer:0,fraction:65535}}).branch,'half');
  assert.throws(()=>bounce(rom,{...input,ballType:32}),RangeError);
});

test('branch and reduced velocity match both captured regular-play shots', {skip:!existsSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc')}, () => {
  const rom = readFileSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc');
  assert.equal(rom.subarray(0x18941,0x1895d).toString('hex'),'bd3600f017c90400b012bd6e00890100d00abd30000aa8b973a8d005');
  assert.equal(rom.readUInt16LE(0xa873 + 2 * 3),0);
  assert.equal(rom.readUInt16LE(0xa873 + 2 * 5),1);
  for (const [file,branch] of [['docs/issd-shot-bounce-audit.json','half'],['docs/issd-shot-type5-bounce-audit.json','seven-eighths']]) {
    const { events } = JSON.parse(readFileSync(file,'utf8'));
    const entry=events.find(e=>e.address==='838941'), after=events.find(e=>e.address==='838866');
    assert.deepEqual(bounce(rom,{ballType:entry.ball_type,flags:entry.flags,velocity:{integer:entry.vz,fraction:entry.vz_frac}}),
      {branch,velocity:{integer:after.vz,fraction:after.vz_frac}});
  }
});
