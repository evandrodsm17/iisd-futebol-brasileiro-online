import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
const wait=source.match(/^function waitForKickoff\(dt,onlineTick=null\)\{[\s\S]*?^\}/m)?.[0];

test('kickoff wait returns before gameplay in both modes and keeps their clock running',()=>{
 assert.ok(wait);
 assert.match(source,/simulationTick\+\+;elapsed\+=dt;\s*if\(waitForKickoff\(dt,pair\.tick\)\)return;/);
 assert.match(source,/const input = captureInputFrame\(keys,bindings,actionQueue\);\s*if\(waitForKickoff\(dt\)\)return;/);
 for(const online of [false,true])for(const before of [false,true]){
  const result=vm.runInNewContext(`(()=>{let elapsed=0,clock=0,camera=0,debug=0;const onlineTest=online?{}:null;
   const resetAt=1000,simulationNow=()=>before?999:1000,advanceMatchClock=()=>clock++,updateCamera=()=>camera++,publishOnlineDebug=()=>debug++;
   ${wait};const waiting=waitForKickoff(1/60,10);return {waiting,elapsed,clock,camera,debug};})()`,{online,before});
  assert.equal(result.waiting,before);assert.equal(result.clock,before?1:0);assert.equal(result.camera,before?1:0);
  assert.equal(result.debug,before&&online?1:0);assert.equal(result.elapsed,before&&!online?1/60:0);
 }
});
