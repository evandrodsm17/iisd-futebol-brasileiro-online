import test from 'node:test';import assert from 'node:assert/strict';import {existsSync,readFileSync} from 'node:fs';
import {recordedPenaltyContact} from './penalty-contact-observed.mjs';
const report=JSON.parse(readFileSync(new URL('./data/issd-penalty-contact-grid.json',import.meta.url),'utf8'));
const local=new URL('./assets/issd/penalty-hitbox-tables-local.json',import.meta.url);
test('captured matrix preserves explicit outcomes without predicting new shots',()=>{
 for(const s of ['left','neutral','right'])for(const k of ['left','neutral','right']){
  const result=recordedPenaltyContact(report,null,s,k);
  assert.equal(result.outcome,s===k?'contact_deferred':'goal_branch');assert.equal(result.contactVerified,null);
  assert.deepEqual(result.before,[1,0]);assert.deepEqual(result.after,s===k?[1,0]:[2,0]);
 }
 assert.throws(()=>recordedPenaltyContact(report,null,'up','left'),RangeError);
});
test('all three captured contacts reproduce native hitbox selection',{skip:!existsSync(local)},()=>{
 const tables=JSON.parse(readFileSync(local,'utf8'));
 for(const direction of ['left','neutral','right'])assert.equal(recordedPenaltyContact(report,tables,direction,direction).contactVerified,true);
});
