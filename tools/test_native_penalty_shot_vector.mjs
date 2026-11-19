import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { nativePenaltyShotVector as vector } from './native_penalty_shot_vector.mjs';

test('variant, direction and flag select the correct signed words', () => {
  const rom = new Uint8Array(0x64000);
  rom.set([0x28, 0, 0x50], 0x63d7c);
  const put = (at, value) => { rom[at] = value & 255; rom[at + 1] = value >>> 8; };
  put(0x63d95 + 0x28, 0x1234);
  put(0x63d8b + 0x28, 0xff00);
  put(0x63da9 + 0x28, 0x0102);
  put(0x63d9f + 0x28, 0xfe00);
  assert.deepEqual(vector(rom, 0, 0x0100, 0x10), {code: 1, base: 0, index: 0, tableOffset: 0x28, dx: 0x1234, dy: -256, dz: 0x102});
  assert.equal(vector(rom, 0, 0x0100, 0).dz, -512);
  assert.equal(vector(rom, 2, 0x0200, 0).tableOffset, 0x58);
  assert.throws(() => vector(rom, 3, 0, 0), RangeError);
  assert.throws(() => vector(new Uint8Array(5), 0, 0, 0), RangeError);
});

test('model matches captured ROM vectors when the local ROM is available', { skip: !existsSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc') || !existsSync('docs/issd-penalty-shot-vector.json') }, () => {
  const rom = readFileSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc');
  const { observations } = JSON.parse(readFileSync('docs/issd-penalty-shot-vector.json', 'utf8'));
  const codeByBase = [1, 9, 8, 10, 2];
  for (const shot of observations) {
    const result = vector(rom, shot.variant, codeByBase[shot.index % 5] << 8, shot.flags);
    assert.deepEqual([result.index, result.tableOffset, result.dx, result.dy, result.dz],
      [shot.index, shot.table_offset, shot.dx, shot.dy, shot.dz]);
  }
});

test('captured inputs drive the observed vectors and resolution routes', { skip: !existsSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc') }, () => {
 const rom=readFileSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc');
 const {shots}=JSON.parse(readFileSync('docs/issd-penalty-shot-chain.json','utf8'));
 assert.equal(shots.length,8);
 assert.equal(shots.filter(shot=>shot.resolution==='deferred').length,2);
 for(const shot of shots){
  const result=vector(rom,shot.variant,shot.input_word,shot.flags);
  assert.deepEqual([result.code,result.base,result.index,result.tableOffset],[shot.code,shot.base,shot.index,shot.table_offset]);
  assert.deepEqual([result.dx,result.dy,result.dz],shot.vector);
  assert.ok(shot.resolved_frame>shot.frame);
 }
});
