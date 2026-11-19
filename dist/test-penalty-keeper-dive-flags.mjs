import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeLateralKeeperDiveFlags} from './penalty-keeper-dive-flags.mjs';
import {nativePenaltyKeeperJump} from './penalty-keeper-jump.mjs';
import {readFileSync} from 'node:fs';
const capture=JSON.parse(readFileSync(new URL('./data/issd-penalty-keeper-motion.json',import.meta.url),'utf8'));
test('lateral animation flag writes match both observed transitions',()=>{
 for(const direction of ['left','right']){
  const samples=capture.captures.find(c=>c.direction===direction).samples;
  const before=samples.find(s=>s.frame===9798),after=samples.find(s=>s.frame===9799);
  assert.equal(nativeLateralKeeperDiveFlags(before.linked_flags),after.linked_flags);
  const jump=nativePenaltyKeeperJump({stateFlags:before.state_flags,linkedFlags:nativeLateralKeeperDiveFlags(before.linked_flags),storedJump:before.stored_jump,vz:before.after.vz});
  assert.equal(jump.vz,after.before.vz);
  assert.equal(jump.storedJump,after.stored_jump);
 }
 assert.equal(nativeLateralKeeperDiveFlags(0xffff),0xfff7);
 assert.throws(()=>nativeLateralKeeperDiveFlags(65536),RangeError);
});
