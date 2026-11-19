import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {replayPenaltySceneScore} from './penalty-scene-score.mjs';
const data=JSON.parse(readFileSync(new URL('./data/issd-penalty-scene-score.json',import.meta.url),'utf8'));
test('each scene uses its own observed shootout history and direct native goal',()=>{
 const left=replayPenaltySceneScore(data.captures[0]),right=replayPenaltySceneScore(data.captures[1]);
 assert.deepEqual(left.steps.map(s=>s.after),[[0,0],[0,1],[1,1]]);
 assert.deepEqual(right.steps.map(s=>s.after),[[1,0],[1,1],[2,1]]);
 assert.equal(left.goalFrameIndex,24);assert.equal(right.goalFrameIndex,23);
});
test('corrupted scores and invented routes cannot enter the replay',()=>{
 const wrong=structuredClone(data.captures[0]);wrong.shots[1].score=[0,0];assert.throws(()=>replayPenaltySceneScore(wrong),RangeError);
 const route=structuredClone(data.captures[0]);route.shots[0].route='defense';assert.throws(()=>replayPenaltySceneScore(route),RangeError);
});
