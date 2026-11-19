import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeLateralKeeperDiveFlags,nativeLateralKeeperLandingFlags,nativeCentralKeeperDiveFlags,nativeCentralKeeperLandingFlags} from './penalty-keeper-dive-flags.mjs';
import {nativePenaltyKeeperJump} from './penalty-keeper-jump.mjs';
import {advanceNativePenaltyKeeper} from './penalty-keeper-motion.mjs';
import {stepLateralKeeperAnimation,stepCentralKeeperAnimation} from './penalty-keeper-animation-gate.mjs';
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
test('landing flag branch matches both recorded lateral dives',()=>{
 for(const direction of ['left','right']){
  const samples=capture.captures.find(c=>c.direction===direction).samples;
  const before=samples.find(s=>s.frame===9818),after=samples.find(s=>s.frame===9819);
  assert.equal(nativeLateralKeeperLandingFlags(before.linked_flags,(before.after.z>>>8)&0xffff),after.linked_flags);
  assert.equal(nativeLateralKeeperLandingFlags(before.linked_flags,0xffff),before.linked_flags);
 }
 assert.throws(()=>nativeLateralKeeperLandingFlags(0,-1),RangeError);
});
test('central animation transition clears the observed low bit and enables the stored jump',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-central-dive.json',import.meta.url),'utf8'));
 const central=capture.captures.find(c=>c.direction==='neutral'),first=central.samples[0],observed=report.observed;
 const transformed=nativeCentralKeeperDiveFlags(observed.flags_low_before);
 assert.equal(transformed&255,observed.flags_low_after);
 assert.equal(transformed&0x2000,observed.linked_flags_after&0x2000);
 const result=nativePenaltyKeeperJump({stateFlags:first.state_flags,linkedFlags:observed.linked_flags_after,storedJump:central.stored_jump,vz:central.initial.vz});
 assert.equal(result.vz,observed.velocity_after);assert.equal(result.vz,first.before.vz);
 const last=central.samples.at(-1),ground=observed.ground_contact;
 assert.equal(last.frame,ground.frame);assert.equal(last.after.z,0);assert.equal(last.after.vz,0);
 assert.equal(nativeCentralKeeperLandingFlags(ground.linked_flags,0),0x10);
 assert.equal(nativeCentralKeeperLandingFlags(ground.linked_flags,0xffff),ground.linked_flags);
 assert.throws(()=>nativeCentralKeeperDiveFlags(-1),RangeError);
});
test('hypothesized central preparation reproduces the captured jump and movement',()=>{
 const recording=capture.captures.find(c=>c.direction==='neutral');
 const evidence=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-central-dive.json',import.meta.url),'utf8')).observed;
 const words=new Map([[0xe76c,0x0101],[0xe76d,0x0001],[0xe75b,0xe778],[0xe77a,0xc9e9],[0xe77c,0xc9ee]]);
 let animation={counter:2,scriptPointer:0xe76b,index:2,tablePointer:0xe75b,variant:0,frameDescriptor:0xc9e4,savedBank:0x81};
 for(let frame=9791;frame<=9794;frame++)animation=stepCentralKeeperAnimation(animation,address=>words.get(address));
 assert.equal(animation.nextState,0x92b8);
 // Only the prior low byte was captured; this test assumes its high byte was zero.
 const flags=nativeCentralKeeperDiveFlags(evidence.flags_low_before);
 let position={...recording.initial};
 const jump=nativePenaltyKeeperJump({stateFlags:recording.samples[0].state_flags,linkedFlags:flags,storedJump:recording.stored_jump,vz:position.vz});
 position.vz=jump.vz;
 for(const sample of recording.samples){
  assert.equal(flags,sample.linked_flags,`frame ${sample.frame}`);
  assert.deepEqual(position,sample.before,`frame ${sample.frame}`);
  position=advanceNativePenaltyKeeper(position,flags);
  assert.deepEqual(position,sample.after,`frame ${sample.frame}`);
 }
 assert.equal(position.z,0);assert.equal(position.vz,0);
});
test('hypothesized animation timing reproduces captured lateral movement and flags',()=>{
 const words=new Map([[0xeddf,0x0303],[0xede0,0x0003],[0xede6,0xedf4],[0xedf6,0xee50],[0xedf8,0xee58]]);
 for(const direction of ['left','right']){
  const recording=capture.captures.find(c=>c.direction===direction);
  let position={...recording.initial},flags=recording.samples[0].linked_flags,storedJump=recording.stored_jump,waiting=true,phase='animation';
  let animation={counter:3,scriptPointer:0xedde,index:2,tablePointer:0xede6,variant:0,frameDescriptor:0xee18,savedBank:0x81};
  for(const sample of recording.samples){
   if(phase==='animation'&&sample.frame>=9790){
    animation=stepLateralKeeperAnimation(animation,address=>words.get(address));
    if(animation.completed)phase='dive-next';
   }else if(phase==='dive-next'){
    flags=nativeLateralKeeperDiveFlags(flags);phase='air';
   }else if(phase==='air'){
    const next=nativeLateralKeeperLandingFlags(flags,(position.z>>>8)&0xffff);
    if(next!==flags){flags=next;phase='landed';}
   }
   if(waiting){
    const jump=nativePenaltyKeeperJump({stateFlags:sample.state_flags,linkedFlags:flags,storedJump,vz:position.vz});
    position.vz=jump.vz;storedJump=jump.storedJump;waiting=jump.nextState==='waiting';
   }
   assert.equal(flags,sample.linked_flags,`${direction} frame ${sample.frame}`);
   assert.equal(storedJump,sample.stored_jump,`${direction} frame ${sample.frame}`);
   assert.deepEqual(position,sample.before,`${direction} frame ${sample.frame}`);
   position=advanceNativePenaltyKeeper(position,flags);
   assert.deepEqual(position,sample.after,`${direction} frame ${sample.frame}`);
  }
  assert.equal(phase,'landed');
 }
});
