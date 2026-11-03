import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

// Exercise the actual canvas drawing branch while keeping the game loop and DOM out.
const source = readFileSync(new URL('./game.js', import.meta.url), 'utf8');
const match = source.match(/^function drawPlayer\(p\) \{.*\}$/m);
assert.ok(match, 'drawPlayer must be available for the rendering regression test');

function render({ actionReady, locomotionReady, active, dynamic = null, descriptor = null, runtime = null, idle = null, motion = 'walking', withBall = false, position = 'MF' }) {
  const calls = [];
  const ctx = Object.fromEntries(['save', 'translate', 'beginPath', 'ellipse', 'fill',
    'arc', 'fillRect', 'fillText', 'restore', 'drawImage'].map(name => [name, (...args) => calls.push([name, ...args])]));
  const sheet = { complete: locomotionReady, naturalWidth: locomotionReady ? 144 : 0, naturalHeight: 48 };
  const actionImage = { complete: actionReady, naturalWidth: actionReady ? 576 : 0 };
  const actor={team: 0,x:0,y:0,number:10,roster:{position},actionVisual:active?{kind:'shot',dir:0,started:0}:null};
  const sandbox = { ctx, Math, playerDirection: () => ({ motion, index:4 }), playerSheet: () => sheet,ball:{owner:withBall?actor:null},idleRenderer:idle,
    actorVisual: { player: { shadowX: 2, shadowY: 1, h: 48, w: 24, offsetX: 0, offsetY: 0 } },
    oamMotionTeams: new Set(), selectedTeamIds: [0, 1], selectedKits: ['home','home'], dynamicLocomotion: dynamic, descriptorLocomotion: descriptor, runtimeBody: runtime, rosterTeam:()=>({kit:{home:{sprite_palette:['#000000']}}}), simulationTick: 0, elapsed: 0,
    actionFrame: () => 0, getActionImage: () => actionImage,
    ACTION_FRAME: { width: 96, height: 96, anchorX: 48, anchorY: 68 },
    locomotionTiming: { walking: [1, 1, 1], running: [1,1,1] }, locomotionFrame: () => 0 };
  const draw = vm.runInNewContext(`(${match[0]})`, sandbox);
  draw(actor);
  return { calls, sheet, actionImage };
}

const action = render({ actionReady: true, locomotionReady: true, active: true });
assert.deepEqual(action.calls.filter(call => call[0] === 'drawImage').map(call => call[1]), [action.actionImage]);
assert.equal(action.calls.filter(call => call[0] === 'fillRect').length, 0, 'fallback must not cover action sprite');
const locomotion = render({ actionReady: false, locomotionReady: true, active: true });
assert.deepEqual(locomotion.calls.filter(call => call[0] === 'drawImage').map(call => call[1]), [locomotion.sheet]);
assert.equal(locomotion.calls.filter(call => call[0] === 'fillRect').length, 0);
const normal = render({ actionReady: true, locomotionReady: true, active: false });
assert.deepEqual(normal.calls.filter(call => call[0] === 'drawImage').map(call => call[1]), [normal.sheet]);
const composed = {};
const dynamic = render({actionReady:false,locomotionReady:true,active:false,dynamic:{frame:()=>composed}});
assert.deepEqual(dynamic.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[composed]);
const dynamicFallback = render({actionReady:false,locomotionReady:true,active:false,dynamic:{frame:()=>null}});
assert.deepEqual(dynamicFallback.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[dynamicFallback.sheet]);
const descriptorFrame={};
const descriptor = render({actionReady:false,locomotionReady:true,active:false,descriptor:{frame:()=>descriptorFrame},dynamic:{frame:()=>composed}});
assert.deepEqual(descriptor.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[descriptorFrame]);
const runtimeFrame={};
const runtime=render({actionReady:false,locomotionReady:true,active:false,runtime:{frame:()=>runtimeFrame}});
assert.deepEqual(runtime.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[runtimeFrame]);
const withoutSheet=render({actionReady:false,locomotionReady:false,active:false,runtime:{frame:()=>runtimeFrame}});
assert.deepEqual(withoutSheet.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[runtimeFrame]);
const idleFrame={},idleRequests=[];
const waiting=render({actionReady:false,locomotionReady:true,active:false,motion:'idle',withBall:true,idle:{frame:request=>{idleRequests.push(request);return idleFrame;}}});
assert.equal(idleRequests[0].withBall,true);assert.equal(idleRequests[0].direction,4);
assert.deepEqual(waiting.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[idleFrame]);
const keeper=render({actionReady:false,locomotionReady:true,active:false,motion:'running',position:'GK',idle:{frame:()=>idleFrame},runtime:{frame:()=>runtimeFrame}});
assert.deepEqual(keeper.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[runtimeFrame],'keeper movement remains animated');
const steerMatch=source.match(/^function steer\(p, tx, ty, running, dt\) \{.*\}$/m);
assert.ok(steerMatch);
const steer=vm.runInNewContext(`(${steerMatch[0]})`,{Math,approachMovement:()=>assert.fail('near target must stop'),moveFixed:()=>assert.fail('near target must not move')});
const settled={x:10,y:10,vx:1,vy:-1};steer(settled,11,10,false,1/60);assert.equal(settled.vx,0);assert.equal(settled.vy,0);
const resetMatch=source.match(/^function reset\(\) \{.*\}$/m);assert.ok(resetMatch);
const resetFixture=vm.runInNewContext(`(()=>{let player={team:0,formationRole:'GK',roster:{position:'GK'}};let outfield={team:0,formationRole:1,roster:{position:'MF'}};let players=[player,outfield],controlled=player,ball={},fieldMidY=100,resetAt=0;const ballFootTarget=()=>({x:0,y:0}),snapCameraToBall=()=>{},simulationNow=()=>0;${resetMatch[0]};reset();return {controlled,player,outfield,ball};})()`,{Object});
assert.equal(resetFixture.controlled,resetFixture.outfield,'kickoff selects an outfield player');
assert.equal(resetFixture.ball.owner,resetFixture.outfield);
const fallback = render({ actionReady: false, locomotionReady: false, active: true });
assert.equal(fallback.calls.filter(call => call[0] === 'drawImage').length, 0);
assert.ok(fallback.calls.some(call => call[0] === 'fillRect'));
console.log('OK: ação, locomoção e desenho de reserva são mutuamente exclusivos');
