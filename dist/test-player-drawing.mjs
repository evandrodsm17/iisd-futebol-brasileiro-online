import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { screenDirectionForVector, directionForAction } from './action-visual.mjs';
import { passDirection } from './pass-direction.mjs';

// Exercise the actual canvas drawing branch while keeping the game loop and DOM out.
const source = readFileSync(new URL('./game.js', import.meta.url), 'utf8');
const match = source.match(/^function drawPlayer\(p\) \{.*\}$/m);
assert.ok(match, 'drawPlayer must be available for the rendering regression test');

function render({ actionReady, locomotionReady, active, actionKind = 'shot', nativePass = null, nativeSlide = null, dynamic = null, descriptor = null, runtime = null, idle = null, goalkeeper = null, motion = 'walking', withBall = false, position = 'MF' }) {
  const calls = [];
  const ctx = Object.fromEntries(['save', 'translate', 'beginPath', 'ellipse', 'fill',
    'arc', 'fillRect', 'fillText', 'restore', 'drawImage'].map(name => [name, (...args) => calls.push([name, ...args])]));
  const sheet = { complete: locomotionReady, naturalWidth: locomotionReady ? 144 : 0, naturalHeight: 48 };
  const actionImage = { complete: actionReady, naturalWidth: actionReady ? 576 : 0 };
  const actor={team: 0,x:0,y:0,number:10,roster:{position},actionVisual:active?{kind:nativeSlide?'slide':nativePass?'pass':actionKind,dir:0,screenDirection:1,started:0,nativePass:!!nativePass,nativeSlide:!!nativeSlide}:null};
  const sandbox = { ctx, Math, displayPlayerDirection: () => ({ motion, index:4 }), playerSheet: () => sheet,ball:{owner:withBall?actor:null},idleRenderer:idle,goalkeeperLocomotion:goalkeeper,
    nativePassBody: nativePass, nativeSlideBody: nativeSlide, actorVisual: { player: { shadowX: 2, shadowY: 1, h: 48, w: 24, offsetX: 0, offsetY: 0 } },
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
const capturedPass={};
const nativePass=render({actionReady:true,locomotionReady:true,active:true,nativePass:{frame:()=>capturedPass,referenceHeight:()=>52}});
assert.deepEqual(nativePass.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[capturedPass],'verified local pass body takes precedence');
const nativeDraw=nativePass.calls.find(call=>call[0]==='drawImage');assert.equal(nativeDraw[4],96*48/52);assert.ok(Math.abs(nativeDraw[3]+68*48/52)<1e-9,'pass anchor remains at player origin');
const capturedSlide={};
const nativeSlide=render({actionReady:true,locomotionReady:true,active:true,nativeSlide:{frame:()=>capturedSlide,referenceHeight:52,duration:30}});
assert.deepEqual(nativeSlide.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[capturedSlide],'captured slide is drawn instead of locomotion');
const slideDraw=nativeSlide.calls.find(call=>call[0]==='drawImage');assert.ok(Math.abs(slideDraw[3]+60*48/52)<1e-9,'slide anchor remains at player origin');
const safeIdle={};
const passFallback=render({actionReady:true,locomotionReady:true,active:true,actionKind:'pass',motion:'idle',idle:{frame:()=>safeIdle}});
assert.deepEqual(passFallback.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[safeIdle],'unverified pass sheets cannot replace player appearance');
const directionMatch=source.match(/function displayPlayerDirection\(p\) \{[\s\S]*?\n\}/);assert.ok(directionMatch);
const directionForPass=vm.runInNewContext(`(${directionMatch[0]})`,{Number,playerDirection:()=>({index:4,motion:'running',fallback:'side'}),romSheetIndexByScreenDirection:[6,7,0,1,2,3,4,5],fallbackByRomSheetIndex:['side','diagonaldown','down','diagonaldown','side','diagonalup','up','diagonalup']});
for(const screen of [1,3,5,7]){const actor={actionVisual:{kind:'pass',nativePass:false,screenDirection:screen}};const actual=directionForPass(actor);assert.equal(actual.index,[6,7,0,1,2,3,4,5][screen]);assert.equal(actual.motion,'idle');assert.equal(actor.facingDirection,screen);}
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
const keeperFrame={};
const keeper=render({actionReady:false,locomotionReady:true,active:false,motion:'running',position:'GK',idle:{frame:()=>idleFrame},goalkeeper:{frame:()=>keeperFrame},runtime:{frame:()=>runtimeFrame}});
assert.deepEqual(keeper.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[keeperFrame],'keeper uses goalkeeper animation');
const keeperMissing=render({actionReady:false,locomotionReady:true,active:false,motion:'running',position:'GK',idle:{frame:()=>idleFrame},goalkeeper:{frame:()=>null},runtime:{frame:()=>runtimeFrame}});
assert.deepEqual(keeperMissing.calls.filter(call=>call[0]==='drawImage').map(call=>call[1]),[idleFrame],'unobserved keeper frame uses keeper idle');
const steerMatch=source.match(/^function steer\(p, tx, ty, running, dt\) \{.*\}$/m);
assert.ok(steerMatch);
const steer=vm.runInNewContext(`(${steerMatch[0]})`,{Math,approachMovement:()=>assert.fail('near target must stop'),moveFixed:()=>assert.fail('near target must not move')});
const settled={x:10,y:10,vx:1,vy:-1};steer(settled,11,10,false,1/60);assert.equal(settled.vx,0);assert.equal(settled.vy,0);
const resetMatch=source.match(/^function reset\(\) \{.*\}$/m);assert.ok(resetMatch);
const resetFixture=vm.runInNewContext(`(()=>{let player={team:0,formationRole:'GK',roster:{position:'GK'}};let outfield={team:0,formationRole:1,roster:{position:'MF'}};let players=[player,outfield],controlled=player,ball={},fieldMidY=100,resetAt=0,trackedOwner=null;const ballFootTarget=()=>({x:0,y:0}),snapCameraToBall=()=>{},simulationNow=()=>0;${resetMatch[0]};reset();return {controlled,player,outfield,ball};})()`,{Object});
assert.equal(resetFixture.controlled,resetFixture.outfield,'kickoff selects an outfield player');
assert.equal(resetFixture.ball.owner,resetFixture.outfield);
const fallback = render({ actionReady: false, locomotionReady: false, active: true });
assert.equal(fallback.calls.filter(call => call[0] === 'drawImage').length, 0);
assert.ok(fallback.calls.some(call => call[0] === 'fillRect'));
const passMatch=source.match(/^function pass\(\) \{.*\}$/m);assert.ok(passMatch);
const passResult=vm.runInNewContext(`(()=>{const controlled={team:0,x:0,y:0,facingDirection:6},ball={owner:controlled},keys=new Set(['right','up']),bindings={right:'right',left:'left',up:'up',down:'down'};let lastTouchTeam,lastKick,visual;const simulationNow=()=>100,resetAt=0,startActionVisual=(actor,kind,direction)=>{visual={actor,kind,direction}};${passMatch[0]};pass();return {controlled,ball,visual};})()`,{Math,screenDirectionForVector,passDirection});
assert.equal(passResult.ball.owner,null);
assert.equal(passResult.visual.kind,'pass');
assert.equal(passResult.visual.direction,1,'pass faces the current directional input');
assert.ok(passResult.ball.vx>0&&passResult.ball.vy<0);
assert.equal(directionForAction('pass',passResult.visual.direction),6,'uncaptured direction uses the existing experimental fallback');
const startMatch=source.match(/^function startActionVisual\(actor, kind, screenDirection\) \{.*\}$/m);assert.ok(startMatch);
const choose=vm.runInNewContext(`(()=>{const selectedTeamIds=[2],selectedKits=['home'],simulationTick=42,rosterTeam=()=>({kit:{home:{sprite_palette:Array(16).fill('#000000')}}}),nativePassBody={supports:r=>r.team===2&&r.screenDirection===2};${startMatch[0]};const actor={team:0,roster:{appearance:{},position:'MF'}};startActionVisual(actor,'pass',2);return actor.actionVisual;})()`,{directionForAction});
assert.equal(choose.nativePass,true);assert.equal(choose.started,42);
const pressMatch=source.match(/^function press\(\) \{.*\}$/m);assert.ok(pressMatch);
const tackle=vm.runInNewContext(`(()=>{const controlled={team:0,roster:{appearance:{skin_tone:0,hair_style:0},position:'DF'},facingDirection:2},ball={owner:{team:1}},keys=new Set(),bindings={right:'right',left:'left',up:'up',down:'down'},selectedTeamIds=[30],selectedKits=['home'],simulationTick=10,nativeSlideBody={supports:()=>true};let lastTackle=-Infinity,lastTouchTeam;const simulationNow=()=>1000,canStealBall=()=>false;${pressMatch[0]};press();return controlled.actionVisual;})()`,{screenDirectionForVector});
assert.equal(tackle.kind,'slide');assert.equal(tackle.nativeSlide,true);assert.equal(tackle.screenDirection,2);
console.log('OK: ação, locomoção e desenho de reserva são mutuamente exclusivos');
