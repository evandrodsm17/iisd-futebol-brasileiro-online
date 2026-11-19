import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

test('accelerated open-match observations preserve their stated limits',()=>{
 const report=JSON.parse(readFileSync('docs/issd-open-match-periods.json','utf8'));
 assert.equal(report.schema,'issd-open-match-periods/v1');
 const cases=Object.fromEntries(report.cases.map(c=>[c.name,c]));
 for(const name of ['draw','home','draw-override0']){
  assert.equal(cases[name].initial.synthetic_clock,true);
  assert.equal(cases[name].initial.home,0);assert.equal(cases[name].initial.away,0);
  assert.ok(cases[name].menu_pulse_count>0);
  assert.ok(cases[name].screenshot_hashes.every(s=>/^[a-f0-9]{64}$/.test(s.sha256)));
 }
 assert.deepEqual(cases.home.active_periods.map(p=>p.phase),[0,1]);
 assert.deepEqual(cases.draw.active_periods.map(p=>p.phase),[0,1,2,3]);
 assert.deepEqual(cases.draw.active_periods.map(p=>p.carrierTeam),[0xe00,0xd00,0xe00,0xd00]);
 assert.deepEqual(cases.draw.active_periods.slice(1).map(p=>p.clock),[0x500,0x300,0x300]);
 assert.equal(cases.home.score_interventions.length,1);
 assert.equal(cases.draw.score_interventions.length,0);
 assert.equal(cases['draw-override0'].overtime_interventions[0].after,0);
 assert.ok(report.limits.some(s=>s.includes('synthetic')));
});
