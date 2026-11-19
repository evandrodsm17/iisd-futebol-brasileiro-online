import test from 'node:test';import assert from 'node:assert/strict';import {existsSync,readFileSync} from 'node:fs';
import {previewPenaltyFreeFlight} from './penalty-free-flight-preview.mjs';
const local=new URL('./assets/issd/penalty-shot-vectors-local.json',import.meta.url);
test('free-flight geometry reaches both captured crossing positions without inventing a result',{skip:!existsSync(local)},()=>{
 const tables=JSON.parse(readFileSync(local,'utf8'));
 for(const [direction,x] of [['left',69],['right',186]]){
  const run=previewPenaltyFreeFlight(tables,direction),last=run.frames.at(-1);
  assert.equal(run.stop,'geometry_reached');assert.equal(run.frames.length,34);
  assert.deepEqual([last.x,last.y,last.height],[x,91,65507]);
  assert.equal(Object.hasOwn(run,'scored'),false);
 }
 for(const direction of ['neutral','up','down','upLeft','upRight','downLeft','downRight']){
  const run=previewPenaltyFreeFlight(tables,direction);assert.ok(run.frames.length>0&&run.frames.length<=90);assert.ok(['geometry_reached','ground_pending','frame_limit'].includes(run.stop));
 }
});
test('unknown inputs and missing vector tables are rejected',()=>{
 assert.throws(()=>previewPenaltyFreeFlight({},'left'),RangeError);
 assert.throws(()=>previewPenaltyFreeFlight({},'other'),RangeError);
});
