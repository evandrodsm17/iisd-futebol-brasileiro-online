import test from 'node:test';import assert from 'node:assert/strict';import {existsSync,readFileSync} from 'node:fs';
import {nativePenaltyVectorFromTables} from './penalty-shot-vector.mjs';
import {nativePenaltyShotVector} from '../tools/native_penalty_shot_vector.mjs';
const local='assets/issd/penalty-shot-vectors-local.json',localUrl=new URL(local,import.meta.url);
const romPath='International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc';
test('local tables reproduce native ROM decoder for all variants, flag paths and input codes',{skip:!existsSync(localUrl)||!existsSync(romPath)},()=>{
 const tables=JSON.parse(readFileSync(localUrl,'utf8'));const rom=readFileSync(romPath);
 for(let variant=0;variant<3;variant++)for(const flags of [0,0x10,0x80,0x90,0xffff])for(let code=0;code<256;code++){
  const inputWord=code<<8;
  assert.deepEqual(nativePenaltyVectorFromTables(tables,variant,inputWord,flags),nativePenaltyShotVector(rom,variant,inputWord,flags));
 }
});
test('malformed manifests and inputs are rejected',()=>{
 assert.throws(()=>nativePenaltyVectorFromTables({},0,0,0),RangeError);
 const tables={schema:'issd-penalty-vectors/v1',rom_revision:'USA',variants:[[],[],[]]};
 assert.throws(()=>nativePenaltyVectorFromTables(tables,3,0,0),RangeError);
 assert.throws(()=>nativePenaltyVectorFromTables(tables,0,0,0),RangeError);
});
