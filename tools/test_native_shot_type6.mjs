import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {nativeType6InitialVertical as initial} from './native_shot_type6.mjs';

test('uses three word tables and clamps the native parameter',()=>{
  const rom=new Uint8Array(0x9f07);
  rom[0x9ebf+22]=0xf9;rom[0x9ebf+23]=0xff;
  rom[0x9ed7+22]=0;rom[0x9ed7+23]=0xc0;
  rom[0x9eef+22]=0;rom[0x9eef+23]=0x24;
  assert.deepEqual(initial(rom,99),{velocity:{integer:0xfff9,fraction:0xc000},gravity:0x2400});
  assert.throws(()=>initial(rom,-1),RangeError);
});

test('type-6 initializer matches recorded natural releases',{skip:!existsSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc')},()=>{
  const rom=readFileSync('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc');
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-type6-init.json','utf8'));
  assert.equal(cases.length,3);
  for(const c of cases) assert.deepEqual(initial(rom,c.parameter),{velocity:{integer:c.vz,fraction:c.vz_fraction},gravity:c.gravity});
});
