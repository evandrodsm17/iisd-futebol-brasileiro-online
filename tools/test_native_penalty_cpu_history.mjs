import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { nativePenaltyCpuHistory as decide } from './native_penalty_cpu_history.mjs';

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
