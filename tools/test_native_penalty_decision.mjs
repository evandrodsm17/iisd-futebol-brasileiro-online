import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { nativePenaltyDecision } from './native_penalty_decision.mjs';

test('native threshold and sudden death cases', () => {
  const check = (home, away, side, round) => nativePenaltyDecision({ home, away, side, round });
  assert.equal(check(3, 0, 2, 2), 0);
  assert.equal(check(2, 0, 2, 2), null);
  assert.equal(check(0, 2, 0, 3), 2);
  assert.equal(check(8, 7, 0, 9), null);
  assert.equal(check(8, 7, 2, 9), 0);
  assert.equal(check(7, 8, 2, 9), 2);
  assert.throws(() => check(2, 1, 1, 2), RangeError);
});

test('captured checks agree with entry to winner branch', { skip: !existsSync('analysis/movement-progression-probe/world-penalty-observe/mode-hooks.jsonl') }, () => {
  const hooks = readFileSync('analysis/movement-progression-probe/world-penalty-observe/mode-hooks.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
  const checks = hooks.map((item, index) => ({ item, index })).filter(({ item }) => item.site === 'penalty_check');
  assert.equal(checks.length, 55);
  for (const [i, { item, index }] of checks.entries()) {
    const end = checks[i + 1]?.index ?? hooks.length;
    const entered = hooks.slice(index + 1, end).some(event => event.site === 'penalty_winner' && event.frame === item.frame);
    const result = nativePenaltyDecision({ home: item.penalty_home, away: item.penalty_away, side: item.side, round: item.round });
    assert.equal(result !== null, entered, `frame ${item.frame}`);
  }
});

test('observed post-attempt checks reach a winner only at the end of this captured sequence', () => {
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-attempt-sequence.json',import.meta.url),'utf8'));
 assert.equal(report.attempts.length,20);
 assert.equal(report.preliminary_winner_branches,6);
 for(const attempt of report.attempts){
  const actual=nativePenaltyDecision({home:attempt.after[0],away:attempt.after[1],side:attempt.native_side,round:attempt.round});
  assert.equal(actual!==null,attempt.winner_branch_after_check,`frame ${attempt.frame}`);
 }
 assert.deepEqual(report.attempts.at(-1).after,[8,7]);
 assert.equal(report.attempts.at(-1).winner_branch_after_check,true);
});

test('crossing resolution precedes the captured post-attempt winner check',()=>{
 const observed=JSON.parse(readFileSync(new URL('../docs/issd-penalty-resolution-path.json',import.meta.url),'utf8'));
 const earlier=JSON.parse(readFileSync(new URL('../docs/issd-penalty-attempt-sequence.json',import.meta.url),'utf8'));
 assert.equal(observed.results.length,20);
 assert.equal(observed.results.filter(item=>item.deferred_finalize).length,3);
 for(const [index,item] of observed.results.entries()){
  const prior=earlier.attempts[index];
  assert.equal(item.frame,prior.frame);assert.equal(item.side,prior.native_side);assert.equal(item.round,prior.round);
  assert.deepEqual(item.score,prior.after);assert.equal(item.goal_branch,prior.increment_observed);
  const decision=nativePenaltyDecision({home:item.score[0],away:item.score[1],side:item.side,round:item.round});
  assert.equal(decision!==null,item.winner_branch);
 }
 assert.equal(observed.results.at(-1).deferred_finalize,true);
 assert.equal(observed.results.at(-1).winner_branch,true);
});
