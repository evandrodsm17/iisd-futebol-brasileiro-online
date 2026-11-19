import test from 'node:test';import assert from 'node:assert/strict';import {existsSync,readFileSync} from 'node:fs';import {recordedPenaltyChecks} from './penalty-contact-timeline.mjs';
const report=JSON.parse(readFileSync(new URL('./data/issd-penalty-contact-timeline.json',import.meta.url),'utf8'));
const motion=JSON.parse(readFileSync(new URL('./data/issd-penalty-keeper-motion.json',import.meta.url),'utf8'));
const local=new URL('./assets/issd/penalty-hitbox-tables-local.json',import.meta.url);
test('six recorded timelines distinguish calls from missing frames',()=>{
 let count=0,hits=0;
 for(const entry of report.cases){const checks=recordedPenaltyChecks(report,null,entry.shooter,entry.keeper);count+=checks.length;hits+=checks.filter(c=>c.hit).length;assert.ok(checks.every(c=>c.verified===null));}
 assert.equal(count,81);assert.equal(hits,3);assert.equal(recordedPenaltyChecks(report,null,'right','left'),null);
 assert.throws(()=>recordedPenaltyChecks(report,null,'up','left'),RangeError);
 const corrupt=structuredClone(report);corrupt.cases[0].initial.vx++;
 assert.throws(()=>recordedPenaltyChecks(corrupt,null,corrupt.cases[0].shooter,corrupt.cases[0].keeper),RangeError);
});
test('calculated keeper positions agree with independent recorded contacts',()=>{
 let calculated=0,recorded=0,initial=0;
 for(const entry of report.cases){
  const checks=recordedPenaltyChecks(report,null,entry.shooter,entry.keeper,motion);
  calculated+=checks.filter(c=>c.keeperSource==='calculated').length;
  recorded+=checks.filter(c=>c.keeperSource==='recorded').length;
  initial+=checks.filter(c=>c.keeperSource==='initial-confirmed').length;
 }
 assert.equal(calculated,57);assert.equal(initial,24);assert.equal(recorded,0);
 for(const [shooter,keeper,expected] of [['left','neutral',11],['neutral','left',9],['right','neutral',11]]){
  assert.equal(recordedPenaltyChecks(report,null,shooter,keeper,motion).filter(c=>c.keeperSource==='calculated').length,expected);
 }
 const bad=structuredClone(motion);const sample=bad.captures.find(c=>c.direction==='left').samples.find(s=>s.frame===report.cases[0].checks[1].frame);sample.before.x+=256;
 assert.throws(()=>recordedPenaltyChecks(report,null,'left','left',bad),RangeError);
 const badFlag=structuredClone(motion);badFlag.captures.find(c=>c.direction==='left').samples.find(s=>s.frame===9799).linked_flags|=8;
 assert.throws(()=>recordedPenaltyChecks(report,null,'left','left',badFlag),RangeError);
 const changed=structuredClone(report);changed.cases[0].checks[0].geometry.x++;
 assert.equal(recordedPenaltyChecks(changed,null,'left','left',motion)[0].keeperSource,'recorded');
});
test('every recorded hit and miss agrees with local native tables',{skip:!existsSync(local)},()=>{
 const tables=JSON.parse(readFileSync(local,'utf8'));
 for(const entry of report.cases)assert.ok(recordedPenaltyChecks(report,tables,entry.shooter,entry.keeper).every(c=>c.verified));
 const bad=structuredClone(report);bad.cases[0].checks[0].hit=!bad.cases[0].checks[0].hit;
 assert.throws(()=>recordedPenaltyChecks(bad,tables,bad.cases[0].shooter,bad.cases[0].keeper),RangeError);
});
