import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createPenaltyShootout,recordPenaltyKick} from './penalty-shootout.mjs';

test('all reachable first-five outcomes match remaining-kicks arithmetic',()=>{
 for(const first of [0,1]){
  let states=[createPenaltyShootout(first)],count=0;
  for(let kick=0;kick<10;kick++){
   const next=[];
   for(const state of states)for(const scored of [false,true]){
    const current=state.nextTeam,result=recordPenaltyKick(state,current,scored);count++;
    const firstAttempts=Math.floor(kick/2)+1,secondAttempts=Math.floor((kick+1)/2);
    const h=result.score[first],a=result.score[1-first];
    const expected=h>a+(5-secondAttempts)?first:a>h+(5-firstAttempts)?1-first:null;
    assert.equal(result.winner,expected,`first=${first}, kick=${kick}, outcomes=${JSON.stringify(result.attempts)}`);
    assert.equal(state.attempts.length,kick,'previous state is not mutated');
    if(expected===null)next.push(result);
    else assert.throws(()=>recordPenaltyKick(result,1-current,true),RangeError);
   }
   states=next;
  }
  assert.ok(count>1000);
 }
});

test('sudden death waits for both teams and alternates after a tie',()=>{
 let state=createPenaltyShootout(1);
 for(let i=0;i<10;i++)state=recordPenaltyKick(state,state.nextTeam,true);
 state=recordPenaltyKick(state,1,true);assert.equal(state.winner,null);
 state=recordPenaltyKick(state,0,true);assert.equal(state.winner,null);
 state=recordPenaltyKick(state,1,true);assert.equal(state.winner,null);
 state=recordPenaltyKick(state,0,false);assert.equal(state.winner,1);
 assert.deepEqual(state.score,[6,7]);
});

test('the observed 20 outcomes lead to the captured 8–7 result',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-attempt-sequence.json',import.meta.url),'utf8'));
 let state=createPenaltyShootout(0);
 for(const item of report.attempts){
  assert.equal(state.nextTeam,item.native_side/2);
  state=recordPenaltyKick(state,state.nextTeam,item.increment_observed);
  assert.deepEqual(state.score,item.after);
  assert.equal(state.winner!==null,item.winner_branch_after_check);
 }
 assert.deepEqual(state.score,[8,7]);assert.equal(state.winner,0);
});

test('rejects out of order and non-boolean outcomes',()=>{
 const state=createPenaltyShootout(0);
 assert.throws(()=>createPenaltyShootout(2),RangeError);
 assert.throws(()=>recordPenaltyKick(state,1,true),RangeError);
 assert.throws(()=>recordPenaltyKick(state,0,1),RangeError);
});
