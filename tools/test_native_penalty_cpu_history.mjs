import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { nativePenaltyCpuHistory as decide, nativePenaltyHistoryWrite as write } from './native_penalty_cpu_history.mjs';

test('native gate, history address and accepted values', () => {
  const history = Array(16).fill(10);
  history[2] = 8;
  const data = { level: 2, gate: 2, random: 2, mask: 15, side: 0, history };
  assert.deepEqual(decide(data), { write: true, direction: 3, index: 2, offset: 0x1764, value: 8 });
  assert.equal(decide({ ...data, side: 2 }).offset, 0x1784);
  assert.equal(decide({ ...data, gate: 7 }).reason, 'gate');
  assert.equal(decide({ ...data, gate: 3 }).reason, 'gate');
  assert.equal(decide({ ...data, random: 1 }).reason, 'history');
  assert.throws(() => decide({ ...data, side: 1 }), RangeError);
});

test('history writes retain other entries and wrap the cursor', () => {
  const history = Array(16).fill(0xffff);
  const result = write({ side: 2, cursor: 30, direction: 5, history });
  assert.equal(result.offset, 0x179e);
  assert.equal(result.cursor, 0);
  assert.equal(result.entries[15], 5);
  assert.equal(result.entries[14], 0xffff);
  assert.equal(history[15], 0xffff);
  assert.throws(() => write({ side: 0, cursor: 1, direction: 0, history }), RangeError);
});

const historyTracePath = 'analysis/movement-progression-probe/world-penalty-history-write/mode-hooks.jsonl';
test('captured writes and cursor advances match', { skip: !existsSync(historyTracePath) }, () => {
  const hooks = readFileSync(historyTracePath, 'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(hooks.at(-1).site, 'session_end');
  const events = hooks.filter(e => ['penalty_history_before', 'penalty_history_after', 'penalty_history_counter'].includes(e.site));
  assert.equal(events.length, 24);
  for (let i = 0; i < events.length; i += 3) {
    const [before, after, counter] = events.slice(i, i + 3);
    const history = Array(16).fill(0xffff);
    history[before.cursor / 2] = before.entry;
    const result = write({ side: before.side, cursor: before.cursor, direction: before.source_direction, history });
    assert.equal(result.offset, before.x);
    assert.equal(result.entries[before.cursor / 2], after.entry);
    assert.equal(result.cursor, counter.cursor);
  }
});

const tracePath = 'analysis/movement-progression-probe/world-penalty-cpu-branches/mode-hooks.jsonl';
test('captured random gates and history outcomes match', { skip: !existsSync(tracePath) }, () => {
  const hooks = readFileSync(tracePath, 'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(hooks.at(-1).site, 'session_end');
  const gates = hooks.filter(e => e.site === 'penalty_cpu_random_gate');
  assert.ok(gates.length >= 4);
  for (const gate of gates) {
    const same = hooks.filter(e => e.frame === gate.frame && e.d === gate.d);
    const pick = same.find(e => e.site === 'penalty_cpu_random_pick');
    const entry = same.find(e => e.site === 'penalty_cpu_history');
    const write = same.find(e => e.site === 'penalty_cpu_write');
    const history = Array(16).fill(0xffff);
    if (pick && entry) history[pick.a & gate.mask] = entry.a;
    const result = decide({ level: gate.level, gate: gate.a, random: pick?.a ?? 0, mask: gate.mask, side: gate.side, history });
    assert.equal(result.write, Boolean(write), `frame ${gate.frame}`);
    if (entry) assert.equal(result.offset, entry.x);
    if (write) assert.equal(result.direction, write.a);
  }
});
