import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

// Exercise the actual canvas drawing branch while keeping the game loop and DOM out.
const source = readFileSync(new URL('./game.js', import.meta.url), 'utf8');
const match = source.match(/^function drawPlayer\(p\) \{.*\}$/m);
assert.ok(match, 'drawPlayer must be available for the rendering regression test');

function render({ actionReady, locomotionReady, active, dynamic = null, descriptor = null }) {
  const calls = [];
  const ctx = Object.fromEntries(['save', 'translate', 'beginPath', 'ellipse', 'fill',
    'arc', 'fillRect', 'fillText', 'restore', 'drawImage'].map(name => [name, (...args) => calls.push([name, ...args])]));
  const sheet = { complete: locomotionReady, naturalWidth: locomotionReady ? 144 : 0, naturalHeight: 48 };
  const actionImage = { complete: actionReady, naturalWidth: actionReady ? 576 : 0 };
  const sandbox = { ctx, Math, playerDirection: () => ({ motion: 'walking' }), playerSheet: () => sheet,
    actorVisual: { player: { shadowX: 2, shadowY: 1, h: 48, w: 24, offsetX: 0, offsetY: 0 } },
    oamMotionTeams: new Set(), selectedTeamIds: [0, 1], selectedKits: ['home','home'], dynamicLocomotion: dynamic, descriptorLocomotion: descriptor, simulationTick: 0, elapsed: 0,
    actionFrame: () => 0, getActionImage: () => actionImage,
    ACTION_FRAME: { width: 96, height: 96, anchorX: 48, anchorY: 68 },
    locomotionTiming: { walking: [1, 1, 1] }, locomotionFrame: () => 0 };
  const draw = vm.runInNewContext(`(${match[0]})`, sandbox);
  draw({ team: 0, x: 0, y: 0, number: 10, actionVisual: active ? {kind: 'shot', dir: 0, started: 0} : null });
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
const fallback = render({ actionReady: false, locomotionReady: false, active: true });
assert.equal(fallback.calls.filter(call => call[0] === 'drawImage').length, 0);
assert.ok(fallback.calls.some(call => call[0] === 'fillRect'));
console.log('OK: ação, locomoção e desenho de reserva são mutuamente exclusivos');
