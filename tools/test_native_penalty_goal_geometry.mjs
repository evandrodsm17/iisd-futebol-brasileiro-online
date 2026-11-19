import test from 'node:test';
import assert from 'node:assert/strict';
import { nativePenaltyGoalGeometry as goal } from './native_penalty_goal_geometry.mjs';

test('native geometry boundaries and unresolved inputs', () => {
  const shot = { x: 0x18, y: 0x5b, height: 0xffb8 };
  assert.equal(goal(shot), true);
  assert.equal(goal({ ...shot, x: 0x17 }), false);
  assert.equal(goal({ ...shot, x: 0xdf }), true);
  assert.equal(goal({ ...shot, x: 0xe0 }), false);
  assert.equal(goal({ ...shot, y: 0x5c }), null);
  assert.equal(goal({ ...shot, height: 0xffb7 }), false);
  assert.equal(goal({ ...shot, height: 0x7fff }), true);
  assert.equal(goal({ ...shot, flags: 0x0800 }), null);
  assert.throws(() => goal({ ...shot, height: -1 }), RangeError);
});

import { readFileSync } from 'node:fs';
import { nativePenaltyGoalGeometryReason as reason } from './native_penalty_goal_geometry.mjs';
test('recorded missed attempts have distinct native routes', () => {
 const geometry=JSON.parse(readFileSync(new URL('../docs/issd-penalty-goal-geometry.json',import.meta.url),'utf8'));
 const result=JSON.parse(readFileSync(new URL('../docs/issd-penalty-resolution-path.json',import.meta.url),'utf8'));
 const misses=geometry.crossings.filter(item=>!item.goal_branch);
 assert.equal(misses.length,5);
 for(const item of misses){
  const route=result.results.find(entry=>entry.frame===item.frame);
  assert.ok(route);
  const r=reason({x:item.x,y:item.y,height:item.height});
  if(route.deferred_finalize) assert.equal(r,'outside_path');
  else assert.equal(r,item.frame===9860?'x_limit':'height_limit');
 }
 assert.equal(reason({x:0x17,y:0x5b,height:0xffb7}),'x_limit','the earlier native X comparison takes precedence');
 assert.equal(reason({x:0x80,y:0x5b,height:0xffb7,flags:0x0800}),'outside_path');
});

test('audited non-scoring routes cover the same captured samples',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-miss-paths.json',import.meta.url),'utf8'));
 assert.equal(report.results.length,5);
 assert.deepEqual(report.results.map(item=>item.route),['native_x_limit','deferred_contact','deferred_contact','native_height_limit','deferred_contact']);
 assert.equal(report.results.at(-1).winner_branch,true);
});
