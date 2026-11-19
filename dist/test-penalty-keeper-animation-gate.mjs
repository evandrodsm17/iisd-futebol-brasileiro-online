import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeLateralKeeperAnimationGate as gate,nativePenaltyAnimationReload as reload,stepLateralKeeperAnimation as step,stepCentralKeeperAnimation as centralStep,nativePenaltyAnimationSelector as select} from './penalty-keeper-animation-gate.mjs';
test('known timer branches follow native word and zero-flag behavior',()=>{
 assert.deepEqual(gate({counter:3,scriptPointer:0x6dde}),{counter:2,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0x6dde}),{counter:0,completed:true,nextState:0x91ac});
 assert.deepEqual(gate({counter:0,scriptPointer:0x6dde}),{counter:65535,completed:false,nextState:0x9196});
 assert.deepEqual(gate({counter:1,scriptPointer:0xedde}),{counter:0,completed:null,nextState:null});
 assert.throws(()=>gate({counter:-1,scriptPointer:0}),RangeError);
});
test('recorded lateral selector writes carry the audited data bank',()=>{
 const audit=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-animation-gate.json',import.meta.url),'utf8'));
 assert.equal(audit.observed.length,2);
 for(const item of audit.observed){
  assert.deepEqual(item.selector_frames,[9792,9795,9799]);
  assert.deepEqual(item.selector_banks,[0x81,0x81,0x81]);
 }
});
test('repeated animation steps reload table entries and eventually enter the dive state',()=>{
 const words=new Map([[0xeddf,0x0303],[0xede0,0x0003],[0xede6,0xedf4],[0xedf6,0xee50],[0xedf8,0xee58]]);
 const read=address=>words.get(address);
 let state={counter:3,scriptPointer:0xedde,index:2,tablePointer:0xede6,variant:0,frameDescriptor:0xee18,savedBank:0x81};
 for(let tick=1;tick<=9;tick++){
  state=step(state,read);
  assert.equal(state.completed,tick===9);
  assert.equal(state.nextState,tick===9?0x91ac:0x9196);
 }
 assert.equal(state.frameDescriptor,0xee58);assert.equal(state.index,6);assert.equal(state.scriptPointer,0x6dde);
 const unknown=step({counter:1,scriptPointer:0xedde,index:2,tablePointer:0xede6,variant:0},read);
 assert.equal(unknown.completed,null);assert.equal(unknown.nextState,null);
 assert.equal(step({counter:1,scriptPointer:0xedde,index:2,tablePointer:0xede6,variant:0,savedBank:0},read).nextState,0x91ac);
});
test('sequence reload reads duration and descriptors before graphics dispatch',()=>{
 const words=new Map([[0xedde,0x0303],[0xeddf,0x0303],[0xede0,0x0003],[0xede6,0xedf4],[0xedf4,0xee18],[0xedf6,0xee50],[0xedf8,0xee58]]);
 const read=address=>words.get(address);
 let state={scriptPointer:0xedde,index:0,tablePointer:0xede6,variant:0};
 for(const [index,descriptor] of [[2,0xee18],[4,0xee50],[6,0xee58]]){
  const next=reload(state,read);assert.equal(next.counter,3);assert.equal(next.index,index);assert.equal(next.frameDescriptor,descriptor);assert.equal(next.completed,null);
  state={...state,scriptPointer:next.scriptPointer,index:next.index};
 }
 assert.equal(state.scriptPointer,0x6dde);
 assert.deepEqual(gate({counter:1,scriptPointer:state.scriptPointer}),{counter:0,completed:true,nextState:0x91ac});
 assert.throws(()=>reload(state,read),RangeError);
 const endWords=new Map([[0x8000,0x0004],[0xffff,0x0100],[0x0100,0x1234]]);
 assert.deepEqual(reload({scriptPointer:0x8000,index:0,tablePointer:0xffff,variant:0},a=>endWords.get(a)),{counter:4,scriptPointer:0,index:0,frameDescriptor:0x9234,completed:null});
 const example={scriptPointer:0xedde,index:0,tablePointer:0xede6,variant:0};
 assert.equal(reload({...example,savedBank:0x81},read).completed,false);
 assert.equal(reload({...example,savedBank:0},read).completed,true);
 assert.throws(()=>reload({...example,savedBank:256},read),RangeError);
});
test('hypothesized starting state reproduces recorded lateral selector changes',()=>{
 const words=new Map([[0xeddf,0x0303],[0xede0,0x0003],[0xede6,0xedf4],[0xedf6,0xee50],[0xedf8,0xee58]]);
 const bytes=new Map([[0xdebb,0],[0xdebd,28],[0xdebf,30],[0xdec2,14],[0xdebc,0xff]]);
 const readWord=address=>words.get(address),readByte=address=>bytes.get(address);
 let state={counter:3,scriptPointer:0xedde,index:2,tablePointer:0xede6,variant:0,frameDescriptor:0xee18,savedBank:0x81};
 let selector=0;const changes=[];
 for(let frame=9790;frame<=9798;frame++){
  state=step(state,readWord);
  const result=select({selector,index:state.index,tableAddress:0xdebb},readByte);
  if(result.changed)changes.push([frame,result.selector]);selector=result.selector;
 }
 assert.equal(state.nextState,0x91ac);
 const next=select({selector,index:2,tableAddress:0xdec2},readByte);
 if(next.changed)changes.push([9799,next.selector]);
 const audit=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-animation-gate.json',import.meta.url),'utf8'));
 for(const capture of audit.observed)assert.deepEqual(changes,capture.selector_frames.map((frame,i)=>[frame,capture.selectors[i]]));
 assert.deepEqual(select({selector:28,index:3,tableAddress:0xdebb},readByte),{selector:28,changed:false,source:0xdebc});
 assert.throws(()=>select({selector:0,index:0,tableAddress:0},()=>256),RangeError);
});
test('hypothesized central sequence matches captured selector transition',()=>{
 const words=new Map([[0xe76c,0x0101],[0xe76d,0x0001],[0xe75b,0xe778],[0xe77a,0xc9e9],[0xe77c,0xc9ee]]);
 const bytes=new Map([[0xdec9,28],[0xdecb,28],[0xdecd,28],[0xded0,20]]);
 const readWord=address=>words.get(address),readByte=address=>bytes.get(address);
 let state={counter:2,scriptPointer:0xe76b,index:2,tablePointer:0xe75b,variant:0,frameDescriptor:0xc9e4,savedBank:0x81};
 let selector=28;const changes=[[9789,selector]];
 // 8C:929C occupies the next recorded frame before 8C:92A2 advances.
 for(let frame=9791;frame<=9794;frame++){
  state=centralStep(state,readWord);
  const result=select({selector,index:state.index,tableAddress:0xdec9},readByte);
  if(result.changed)changes.push([frame,result.selector]);selector=result.selector;
 }
 assert.equal(state.nextState,0x92b8);
 const next=select({selector,index:2,tableAddress:0xded0},readByte);
 if(next.changed)changes.push([9795,next.selector]);
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-keeper-central-animation.json',import.meta.url),'utf8'));
 assert.deepEqual(changes,report.observed.frames.map((frame,i)=>[frame,report.observed.selectors[i]]));
 assert.equal(centralStep({counter:2,scriptPointer:0xe76b,index:2,tablePointer:0xe75b,variant:0},readWord).nextState,0x92a2);
 assert.equal(centralStep({counter:1,scriptPointer:0xe76b,index:2,tablePointer:0xe75b,variant:0},readWord).nextState,null);
});
