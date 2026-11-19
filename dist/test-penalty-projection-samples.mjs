import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeOamProjectionPart} from './native-oam-projection.mjs';
const samples=JSON.parse(readFileSync(new URL('./data/issd-penalty-projection-samples.json',import.meta.url),'utf8'));
test('browser projection reproduces all 78 pixel-validated captured positions',()=>{
 let count=0;
 for(const capture of samples.captures) for(const frame of capture.frames) if(frame){
  const p=nativeOamProjectionPart(frame);
  assert.equal(p.x&255,frame.oamX);assert.equal(p.y&255,frame.oamY);count++;
 }
 assert.equal(count,78);
});
