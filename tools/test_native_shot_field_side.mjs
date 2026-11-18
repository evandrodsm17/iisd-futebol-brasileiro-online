import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeShotFieldSide as side} from './native_shot_field_side.mjs';
import {nativeShotReleaseBranch as release} from './native_shot_release_branch.mjs';

test('native flag selection preserves wrapping, orientation and boundary equality', () => {
  assert.deepEqual(side(0,10,10),{flags:0x800,carry:true});
  assert.deepEqual(side(1,10,10),{flags:1,carry:false});
  assert.deepEqual(side(1,647,928),{flags:0x801,carry:true});
  assert.deepEqual(side(0x800,0,0xffff),{flags:0x800,carry:true});
  assert.throws(()=>side(-1,0,0),RangeError);
});

test('models match the control and explicitly modified branch experiments', () => {
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-synthetic-branches.json','utf8'));
  assert.deepEqual(cases.map(c=>c.ball_type),[5,3,6]);
  for(const c of cases){
    assert.equal(side(c.flags_before,c.actor_coordinate,c.boundary).carry,c.branch_set);
    const result=release(c.release_flags,c.post_helper_word??0,c.charge);
    assert.equal(result.ballType,c.ball_type);
    assert.equal(result.parameter,c.parameter);
  }
});

test('six captured field checks and subsequent release choices agree', () => {
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-release-detail.json','utf8'));
  assert.equal(cases.length,6);
  for(const c of cases){
    const actual=side(c.flags_before,c.actor_coordinate,c.boundary);
    assert.equal(actual.carry,c.branch_set);
    assert.equal(actual.flags&0x800,c.release_flags&0x800);
    assert.equal(c.post_helper_word&1,0);
    assert.equal(c.ball_type,5);
  }
});
