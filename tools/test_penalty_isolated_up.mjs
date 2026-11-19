import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {nativePenaltyShotDirection} from '../dist/penalty-direction.mjs';
const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-isolated-up.json',import.meta.url),'utf8'));
test('isolated Up captures retain gate evidence and decoded shot directions',()=>{
 assert.deepEqual(report.runs.map(run=>run.controller),['p1','p2']);
 for(const run of report.runs){
  assert.ok(run.input_samples>0);assert.equal(run.gate_frame,run.shots[0].frame);assert.equal(run.shots.length,4);
  for(const shot of run.shots)assert.equal(nativePenaltyShotDirection(shot.input_word,shot.flags).index,shot.index);
 }
 const [p1,p2]=report.runs;
 assert.equal(p1.shots[2].input_word,0x800);assert.equal(p2.shots[2].input_word,0);
 assert.deepEqual(p1.shots[2].vector,p2.shots[2].vector);
});
