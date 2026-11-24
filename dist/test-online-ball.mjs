import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceOnlineBall,resolveOnlineFieldExit} from './online-ball.mjs';
import {ballFootTarget} from './dribble-contact.mjs';
import {Y_NATIVE_PER_WORLD} from './ball-contact.mjs';
import {advanceShotAirborne} from './shot-model.mjs';
import {releaseHeldGoalkeeperPass} from './goalkeeper-model.mjs';

test('online shots follow the local airborne update and cannot be picked up in flight',()=>{
 const opponent={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:0,vx:2,vy:0,vz:-2,gravity:.14,owner:null,actionKind:'shot'};
 const expected=advanceShotAirborne(ball);
 advanceOnlineBall(ball,[opponent],1,0,1000);
 assert.equal(ball.z,expected.z);assert.equal(ball.vz,expected.vz);
 assert.equal(ball.vx,2);assert.equal(ball.owner,null);
});

test('online shot bounces without ground friction or immediate pickup',()=>{
 const opponent={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:98,y:50,z:-0.1,vx:2,vy:0,vz:1,gravity:.14,owner:null,actionKind:'shot'};
 advanceOnlineBall(ball,[opponent],1,0,1000);
 assert.equal(ball.z,0);assert.ok(Math.abs(ball.vz+.855)<1e-12);
 assert.equal(ball.vx,2);assert.equal(ball.owner,null);
});

test('online shot eventually settles and can be recovered',()=>{
 const opponent={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:-.1,vx:0,vy:0,vz:.1,gravity:.14,owner:null,actionKind:'shot'};
 advanceOnlineBall(ball,[opponent],1,0,1000);
 assert.equal(ball.z,0);assert.equal(ball.vz,0);assert.equal(ball.owner,opponent);
});

test('airborne online shot crosses the boundary before pickup',()=>{
 const field={x:0,y:0,w:200,h:100,goalH:40},opponent={team:1,x:100,y:-6,vx:0,vy:0};
 const ball={x:100,y:0,z:-8,vx:0,vy:-6,vz:-1,gravity:.14,owner:null,actionKind:'shot'};
 const before={x:ball.x,y:ball.y,z:ball.z};
 advanceOnlineBall(ball,[opponent],1,0,1000,undefined,field);
 assert.equal(ball.owner,null);
 const event=resolveOnlineFieldExit(before,ball,field,0,{goal:()=>{},restart:()=>{}});
 assert.equal(event.type,'throw_in');
});

test('keeps the ball with its carrier using the existing dribble model',()=>{
 const player={team:0,x:100,y:100,vx:1,vy:0,facingDirection:2};
 const ball={...ballFootTarget(player),z:0,vx:0,vy:0,owner:player};
 player.x+=3;const last=advanceOnlineBall(ball,[player],1,1,1000);
 assert.equal(last,0);assert.equal(ball.owner,player);assert.ok(ball.x>110.5);
});
test('loose ball can be recovered by the other human player',()=>{
 const first={team:0,x:50,y:50,vx:0,vy:0},second={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:0,vx:0,vy:0,owner:null};
 assert.equal(advanceOnlineBall(ball,[first,second],1,0,1000),1);
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

test('a teammate can receive a goalkeeper pass in the air after the existing cooldown',()=>{
 const receiver={team:0,x:100,y:50,vx:0,vy:0,facingDirection:2};
 const ball={x:100,y:50,z:-8,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'keeper_throw'};
 assert.equal(advanceOnlineBall(ball,[receiver],1,0,100),0);assert.equal(ball.owner,null);
 assert.equal(advanceOnlineBall(ball,[receiver],1,0,300),0);assert.equal(ball.owner,receiver);assert.equal(ball.actionKind,null);
});

test('a nearby teammate can receive immediately without the keeper recovering his own throw',()=>{
 const keeper={team:0,x:100,y:50,roster:{position:'GK'}},teammate={team:0,x:104,y:50,vx:0,vy:0};
 const ball={owner:keeper,keeperHeld:true,x:100,y:50,z:0};
 releaseHeldGoalkeeperPass(ball,keeper,{x:1,y:0},1);
 assert.equal(advanceOnlineBall(ball,[keeper,teammate],1,0,50),0);
 assert.equal(ball.owner,teammate);assert.equal(ball.keeperThrower,null);
 const alone={owner:keeper,keeperHeld:true,x:100,y:50,z:0};
 releaseHeldGoalkeeperPass(alone,keeper,{x:1,y:0},1);
 advanceOnlineBall(alone,[keeper],1,0,50);assert.equal(alone.owner,null);
 advanceOnlineBall(alone,[keeper],1,0,300);assert.equal(alone.owner,keeper);
 const opponent={team:1,x:101,y:50,vx:0,vy:0},intercept={owner:keeper,keeperHeld:true,x:100,y:50,z:0};
 releaseHeldGoalkeeperPass(intercept,keeper,{x:1,y:0},1);
 assert.equal(advanceOnlineBall(intercept,[keeper,teammate,opponent],1,0,50),1);assert.equal(intercept.owner,opponent);
});

test('a grounded goalkeeper distribution keeps the thrower-only cooldown for both teams',()=>{
 for(const team of [0,1]){
  const keeper={team,x:100,y:50,roster:{position:'GK'}},teammate={team,x:104,y:50,vx:0,vy:0};
  const ball={owner:null,keeperThrower:keeper,keeperHeld:false,actionKind:'keeper_throw',x:101,y:50,z:0,vx:0,vy:0,vz:0,gravity:.125};
  assert.equal(advanceOnlineBall(ball,[keeper,teammate],1,team,50),team);
  assert.equal(ball.owner,teammate,'companheiro pode receber mesmo após a bola tocar o chão');
  const alone={...ball,owner:null,keeperThrower:keeper,actionKind:'keeper_throw'};
  advanceOnlineBall(alone,[keeper],1,team,50);assert.equal(alone.owner,null);
  advanceOnlineBall(alone,[keeper],1,team,300);assert.equal(alone.owner,keeper);
  const unknown={...ball,owner:null,keeperThrower:null,actionKind:'keeper_throw'};
  advanceOnlineBall(unknown,[teammate],1,team,50);assert.equal(unknown.owner,null,'origem desconhecida mantém a política anterior');
 }
});

test('a goalkeeper pass crossing a boundary cannot be received beyond it',()=>{
 const field={x:0,y:0,w:200,h:100,goalH:40},opponent={team:1,x:100,y:-6,vx:0,vy:0};
 const ball={x:100,y:0,z:-8,vx:0,vy:-6,vz:0,gravity:.125,owner:null,actionKind:'keeper_throw'};
 assert.equal(advanceOnlineBall(ball,[opponent],1,0,1000,undefined,field),0);assert.equal(ball.owner,null);
});

test('an opponent can intercept a goalkeeper pass before the same-team cooldown ends',()=>{
 const opponent={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:100,y:50,z:-8,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'keeper_throw'};
 assert.equal(advanceOnlineBall(ball,[opponent],1,0,100),1);assert.equal(ball.owner,opponent);
});

test('a throw beginning its bounce is not slowed or picked up as grounded',()=>{
 const player={team:1,x:100,y:50,vx:0,vy:0};
 const ball={x:98,y:50,z:-0.1,vx:2,vy:0,vz:1,gravity:.125,owner:null,actionKind:'throw_in'};
 assert.equal(advanceOnlineBall(ball,[player],1,0,1000),0);
 assert.equal(ball.z,0);assert.ok(ball.vz<0);assert.equal(ball.vx,2);
 assert.equal(ball.owner,null);assert.equal(ball.actionKind,'throw_in');
});

test('goalkeeper distribution loses horizontal speed on every bounce and then rolls to a stop',()=>{
 for(const sign of [-1,1]){
  const ball={x:0,y:0,z:-0.1,vx:4*sign,vy:-2*sign,vz:1,gravity:.125,owner:null,actionKind:'keeper_throw'};
  let bounces=0;
  for(let i=0;i<500;i++){
   const previous={vx:ball.vx,vy:ball.vy,vz:ball.vz};
   advanceOnlineBall(ball,[],1,0,1000);
   if(previous.vz>0&&ball.vz<0){
    bounces++;
    assert.equal(ball.vx,previous.vx*.75);assert.equal(ball.vy,previous.vy*.75);
   }
   if(ball.z===0&&ball.vz===0&&ball.vx===0&&ball.vy===0)break;
  }
  assert.ok(bounces>=2);assert.equal(ball.z,0);assert.equal(ball.vz,0);assert.equal(Math.abs(ball.vx),0);assert.equal(Math.abs(ball.vy),0);
 }
});

test('online airborne receipt forwards side and pre-contact native-height context',()=>{
 const receiver={team:1,x:100,y:50,vx:0,vy:0,facingDirection:5};
 const ball={x:100,y:50,z:-23/Y_NATIVE_PER_WORLD,vx:0,vy:0,vz:0,gravity:.125,owner:null,actionKind:'throw_in',throwInSide:'lower',throwInPower:'pass',throwInTeam:1};
 let seen=null;advanceOnlineBall(ball,[receiver],1,0,1000,(player,context)=>{seen={player,context};});
 assert.equal(seen.player,receiver);assert.deepEqual(seen.context,{side:'lower',power:'pass',sourceTeam:1,nativeHeight:0xffe9});
 assert.equal(ball.owner,receiver);assert.equal(ball.z,0);
});
