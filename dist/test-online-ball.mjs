import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceOnlineBall,resolveOnlineFieldExit} from './online-ball.mjs';
import {ballFootTarget} from './dribble-contact.mjs';
import {Y_NATIVE_PER_WORLD} from './ball-contact.mjs';

test('keeps the ball with its carrier using the existing dribble model',()=>{
 const player={team:0,x:100,y:100,vx:1,vy:0,facingDirection:2};
 const ball={...ballFootTarget(player),z:0,vx:0,vy:0,owner:player};
 player.x+=3;const last=advanceOnlineBall(ball,[player],1,1,1000);
 assert.equal(last,0);assert.equal(ball.owner,player);assert.ok(ball.x>110.5);
});
test('loose ball can be recovered by the other human player',()=>{
 const first={team:0,x:50,y:50,vx:0,vy:0},second={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:0,vx:0,vy:0,owner:null};
 assert.equal(advanceOnlineBall(ball,[first,second],1,0,1000),0);
 assert.equal(ball.owner,second);
 assert.equal(advanceOnlineBall(ball,[first,second],1,0,1000),1);
});

test('rolling passes use the local pass friction and respect pickup delay',()=>{
 const player={team:0,x:100,y:100,vx:0,vy:0},ball={x:100,y:100,z:0,vx:2,vy:0,owner:null,passRolling:true};
 advanceOnlineBall(ball,[player],1,0,100);assert.equal(ball.owner,null);assert.ok(Math.abs(ball.vx-1.96)<1e-12);
 advanceOnlineBall(ball,[player],1,0,300);assert.equal(ball.owner,player);
 advanceOnlineBall(ball,[player],1,0,300);assert.equal(ball.passRolling,false);
});

test('dispatches goals and all restart types using the existing field rules',()=>{
 const field={x:0,y:0,w:200,h:100,goalH:40},calls=[];
 const handlers={goal:team=>calls.push(['goal',team]),restart:(kind,x,y,team)=>calls.push([kind,team])};
 const ball=(x,y)=>({x,y,z:0});
 resolveOnlineFieldExit(ball(100,5),ball(100,-10),field,0,handlers);
 resolveOnlineFieldExit(ball(190,10),ball(210,10),field,1,handlers);
 resolveOnlineFieldExit(ball(190,10),ball(210,10),field,0,handlers);
 resolveOnlineFieldExit(ball(190,50),ball(210,50),field,0,handlers);
 assert.deepEqual(calls,[['LATERAL',1],['ESCANTEIO',0],['TIRO DE META',1],['goal',0]]);
});

test('line crossing wins over a grounded pickup at the end of the online step',()=>{
 const field={x:0,y:0,w:200,h:100,goalH:40},opponent={team:1,x:100,y:-6,vx:0,vy:0};
 const ball={x:100,y:0,z:0,vx:0,vy:-6,vz:0,owner:null,passRolling:true};
 const previous={x:ball.x,y:ball.y,z:ball.z};
 const last=advanceOnlineBall(ball,[opponent],1,0,1000,undefined,field);
 assert.equal(ball.owner,null);assert.equal(last,0);assert.equal(ball.vy,-6);
 const calls=[],event=resolveOnlineFieldExit(previous,ball,field,last,{goal:()=>{},restart:(kind,x,y,team)=>calls.push([kind,team])});
 assert.equal(event.type,'throw_in');assert.deepEqual(calls,[['LATERAL',1]]);
});

test('line crossing wins over a throw reception at the end of the online step',()=>{
 const field={x:0,y:0,w:200,h:100,goalH:40},opponent={team:1,x:100,y:-6,vx:0,vy:0};
 const ball={x:100,y:0,z:-8,vx:0,vy:-6,vz:0,gravity:.125,owner:null,actionKind:'throw_in'};
 let received=false;const last=advanceOnlineBall(ball,[opponent],1,0,1000,()=>{received=true;},field);
 assert.equal(ball.owner,null);assert.equal(last,0);assert.equal(received,false);assert.equal(ball.y,-6);
});

test('online throw stays airborne, bounces and permits ground pickup',()=>{
 const opponent={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:-22,vx:0,vy:0,vz:-1.875,gravity:.125,owner:null,actionKind:'throw_in'};
 advanceOnlineBall(ball,[opponent],1,0,1000);
 assert.equal(ball.owner,null);assert.ok(ball.z<0);
 let bounced=false;
 for(let i=0;i<200&&ball.actionKind;i++){
  const previous=ball.vz;advanceOnlineBall(ball,[],1,0,1000);
  if(previous>0&&ball.vz<0)bounced=true;
 }
 assert.equal(bounced,true);assert.equal(ball.z,0);
 advanceOnlineBall(ball,[opponent],1,0,1000);assert.equal(ball.owner,opponent);
});

test('online receiver can collect a throw while it is airborne',()=>{
 const receiver={team:1,x:100,y:50,vx:0,vy:0,facingDirection:2};
 const ball={x:100,y:50,z:-8,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'throw_in'};
 assert.equal(advanceOnlineBall(ball,[receiver],1,0,1000),1);
 assert.equal(ball.owner,receiver);assert.equal(ball.z,0);assert.equal(ball.actionKind,null);
});

test('a throw beginning its bounce is not slowed or picked up as grounded',()=>{
 const player={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:98,y:50,z:-0.1,vx:2,vy:0,vz:1,gravity:.125,owner:null,actionKind:'throw_in'};
 assert.equal(advanceOnlineBall(ball,[player],1,0,1000),0);
 assert.equal(ball.z,0);assert.ok(ball.vz<0);assert.equal(ball.vx,2);
 assert.equal(ball.owner,null);assert.equal(ball.actionKind,'throw_in');
});

test('online airborne receipt forwards side and pre-contact native-height context',()=>{
 const receiver={team:1,x:100,y:50,vx:0,vy:0,facingDirection:5};
 const ball={x:100,y:50,z:-23/Y_NATIVE_PER_WORLD,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'throw_in',throwInSide:'lower',throwInPower:'pass',throwInTeam:1};
 let seen=null;advanceOnlineBall(ball,[receiver],1,0,1000,(player,context)=>{seen={player,context};});
 assert.equal(seen.player,receiver);assert.deepEqual(seen.context,{side:'lower',power:'pass',sourceTeam:1,nativeHeight:0xffe9});
 assert.equal(ball.owner,receiver);assert.equal(ball.z,0);
});
