import test from 'node:test';import assert from 'node:assert/strict';import {existsSync,readFileSync} from 'node:fs';import {recordedPenaltyChecks} from './penalty-contact-timeline.mjs';
const report=JSON.parse(readFileSync(new URL('./data/issd-penalty-contact-timeline.json',import.meta.url),'utf8'));
const local=new URL('./assets/issd/penalty-hitbox-tables-local.json',import.meta.url);
test('six recorded timelines distinguish calls from missing frames',()=>{
 let count=0,hits=0;
 for(const entry of report.cases){const checks=recordedPenaltyChecks(report,null,entry.shooter,entry.keeper);count+=checks.length;hits+=checks.filter(c=>c.hit).length;assert.ok(checks.every(c=>c.verified===null));}
 assert.equal(count,81);assert.equal(hits,3);assert.equal(recordedPenaltyChecks(report,null,'right','left'),null);
 assert.throws(()=>recordedPenaltyChecks(report,null,'up','left'),RangeError);
});
test('every recorded hit and miss agrees with local native tables',{skip:!existsSync(local)},()=>{
 const tables=JSON.parse(readFileSync(local,'utf8'));
 for(const entry of report.cases)assert.ok(recordedPenaltyChecks(report,tables,entry.shooter,entry.keeper).every(c=>c.verified));
 const bad=structuredClone(report);bad.cases[0].checks[0].hit=!bad.cases[0].checks[0].hit;
 assert.throws(()=>recordedPenaltyChecks(bad,tables,bad.cases[0].shooter,bad.cases[0].keeper),RangeError);
});
