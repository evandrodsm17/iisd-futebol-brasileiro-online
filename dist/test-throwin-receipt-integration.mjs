import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {advanceOnlineBall} from './online-ball.mjs';
import {Y_NATIVE_PER_WORLD} from './ball-contact.mjs';
import {canShowCapturedReceipt,canShowContestedReceipt} from './throwin-receipt-visual.mjs';

// Exercise the real game callback with the real online ball update. The ROM
// assets are optional, so a strict renderer stub represents their availability.
test('eligible online airborne contact starts the captured visual',()=>{
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const request=source.match(/^function throwVisualRequest\(actor,screenDirection\)\{.*\}$/m);
 const callback=source.match(/^function startCapturedThrowReceipt\(actor,context\)\{[\s\S]*?^\}/m);
 assert.ok(request&&callback);assert.match(source,/advanceOnlineBall\(ball,humanPlayers,dt\*60,lastTouchTeam,simulationNow\(\)-lastKick,startCapturedThrowReceipt\)/);
 assert.match(source,/collectAirborneThrow\(players\.filter\(p=>!isFallen\(p,simulationTick\)\),ball,lastTouchTeam,simulationNow\(\)-lastKick,startCapturedThrowReceipt\)/);
 const context={selectedTeamIds:[26,3],selectedKits:['home','away'],rosterTeam:()=>({kit:{away:{sprite_palette:[]}}}),pitchView:()=>({active:false}),nativeReceiptBody:{supports:r=>r.screenDirection===3},canShowCapturedReceipt,simulationTick:123};
 const handler=vm.runInNewContext(`${request[0]}\n${callback[0]}\nstartCapturedThrowReceipt`,context);
 const receiver={team:1,x:100,y:50,vx:0,vy:0,facingDirection:5,roster:{position:'MF',appearance:{skin_tone:0,hair_style:0},shirt_number:5}};
 const ball={x:100,y:50,z:-23/Y_NATIVE_PER_WORLD,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'throw_in',throwInSide:'lower',throwInPower:'pass',throwInTeam:1};
 advanceOnlineBall(ball,[receiver],1,0,1000,handler);
 assert.equal(ball.owner,receiver);assert.equal(receiver.receiptVisual.started,123);assert.equal(receiver.receiptVisual.request.screenDirection,3);
});

test('eligible opposing airborne contact starts the contested visual',()=>{
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const request=source.match(/^function throwVisualRequest\(actor,screenDirection\)\{.*\}$/m);
 const callback=source.match(/^function startCapturedThrowReceipt\(actor,context\)\{[\s\S]*?^\}/m);
 const context={selectedTeamIds:[26,11],selectedKits:['home','home'],rosterTeam:()=>({kit:{home:{sprite_palette:[]}}}),pitchView:()=>({active:false}),nativeReceiptBody:{supports:()=>false,referenceHeight:()=>52},nativeContestedReceiptBody:{supports:r=>r.screenDirection===2},canShowCapturedReceipt,canShowContestedReceipt,simulationTick:321};
 const handler=vm.runInNewContext(`${request[0]}\n${callback[0]}\nstartCapturedThrowReceipt`,context);
 const receiver={team:1,x:100,y:50,vx:0,vy:0,facingDirection:4,roster:{position:'MF',appearance:{skin_tone:0,hair_style:0},shirt_number:6}};
 const ball={x:100,y:50,z:-18/Y_NATIVE_PER_WORLD,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'throw_in',throwInSide:'lower',throwInPower:'shot',throwInTeam:0};
 advanceOnlineBall(ball,[receiver],1,0,1000,handler);
 assert.equal(ball.owner,receiver);assert.equal(receiver.receiptVisual.started,321);assert.equal(receiver.receiptVisual.kind,'contested');assert.equal(receiver.receiptVisual.request.screenDirection,2);
});
