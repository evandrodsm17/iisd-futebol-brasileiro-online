import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {replayPenaltyCapture} from './penalty-capture-replay.mjs';
const data=JSON.parse(readFileSync(new URL('./data/issd-penalty-replay.json',import.meta.url),'utf8'));
test('captured shootout reproduces each score and delayed outcomes',()=>{
 const steps=replayPenaltyCapture(data);
 assert.deepEqual(steps.map(s=>s.score),[[1,0],[1,1],[2,1],[2,2],[2,2],[2,3],[2,3],[2,4]]);
 assert.deepEqual(steps.map(s=>s.checks),[0,0,0,0,39,0,39,0]);
 assert.equal(steps.at(-1).winner,1);
});
test('inconsistent captured score is rejected',()=>{
 const corrupt=structuredClone(data);corrupt.cases[0].score=[0,0];
 assert.throws(()=>replayPenaltyCapture(corrupt),RangeError);
});
