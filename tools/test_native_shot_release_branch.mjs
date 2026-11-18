import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeShotReleaseBranch as select} from './native_shot_release_branch.mjs';

test('shot branch uses the entry flag and post-helper actor word', () => {
  assert.deepEqual(select(0,1,7),{ballType:3,parameter:11,path:'85F871'});
  assert.deepEqual(select(0x800,0,5),{ballType:5,parameter:5,path:'85F89B'});
  assert.deepEqual(select(0x800,1,5),{ballType:6,parameter:5,path:'85F89B'});
  assert.throws(()=>select(0,-1,0),RangeError);
});

test('two captured release paths match the selector', () => {
  const {cases}=JSON.parse(readFileSync('docs/issd-shot-release-context.json','utf8'));
  for (const [name,postHelperWord] of [['right',0],['left',0]]) {
    const e=cases[name].release, result=select(e.flags6e,postHelperWord,e.charge);
    assert.deepEqual(result,{ballType:e.x,parameter:e.y,path:e.site});
  }
});
