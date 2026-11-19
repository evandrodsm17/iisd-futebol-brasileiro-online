import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {observedPenaltyAimWord} from '../dist/penalty-observed-input.mjs';
import {nativePenaltyShotDirection} from '../dist/penalty-direction.mjs';
const replay=JSON.parse(readFileSync(new URL('../docs/issd-penalty-direction-replay.json',import.meta.url),'utf8'));
const key={neutral:'neutral',Left:'left',Right:'right',Up:'up',Down:'down',UpLeft:'upLeft',UpRight:'upRight',DownLeft:'downLeft',DownRight:'downRight'};
test('eight isolated directions and neutral reproduce native word and index in captured shot',()=>{
 const runs=replay.runs.filter(run=>run.controller==='p1');assert.equal(runs.length,9);
 for(const shot of runs){assert.equal(shot.input_word,observedPenaltyAimWord(key[shot.direction]));assert.equal(nativePenaltyShotDirection(shot.input_word,shot.flags).index,shot.index);}
 assert.throws(()=>observedPenaltyAimWord('toString'),RangeError);assert.throws(()=>observedPenaltyAimWord('up+down'),RangeError);
});
test('left on second controller did not alter the captured shooter word',()=>{
 const shot=replay.runs.find(run=>run.direction==='Left'&&run.controller==='p2');assert.equal(shot.input_word,observedPenaltyAimWord('neutral'));
});
