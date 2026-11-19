import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {observedPenaltyAimWord} from '../dist/penalty-observed-input.mjs';
import {nativePenaltyShotDirection} from '../dist/penalty-direction.mjs';
const horizontal=JSON.parse(readFileSync(new URL('../docs/issd-penalty-isolated-horizontal.json',import.meta.url),'utf8'));
const vertical=JSON.parse(readFileSync(new URL('../docs/issd-penalty-isolated-up.json',import.meta.url),'utf8'));
test('isolated shooter inputs reproduce the observed native word and index for one matched shot',()=>{
 for(const direction of ['left','right']){
  const run=horizontal.runs.find(r=>r.direction.toLowerCase()===direction&&r.controller==='p1');const shot=run.shots[2];
  assert.equal(shot.input_word,observedPenaltyAimWord(direction));assert.equal(nativePenaltyShotDirection(shot.input_word,shot.flags).index,shot.index);
  const other=horizontal.runs.find(r=>r.direction.toLowerCase()===direction&&r.controller==='p2');assert.equal(other.shots[2].input_word,observedPenaltyAimWord('neutral'));
 }
 const up=vertical.runs.find(r=>r.controller==='p1').shots[2];assert.equal(up.input_word,observedPenaltyAimWord('up'));
 assert.throws(()=>observedPenaltyAimWord('down'),RangeError);assert.throws(()=>observedPenaltyAimWord('toString'),RangeError);
});
