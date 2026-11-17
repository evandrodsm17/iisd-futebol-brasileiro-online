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
