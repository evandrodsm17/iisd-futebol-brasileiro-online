import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceOnlineBall,resolveOnlineFieldExit} from './online-ball.mjs';
import {resolveOnlineGoalkeeperShot} from './online-goalkeeper.mjs';
import {goalkeeperShotContact,settleHeldGoalkeeperBall,releaseHeldGoalkeeperPass} from './goalkeeper-model.mjs';
import {classifyFieldExitWithTime} from './field-events.mjs';
import {canStealBall} from './ball-steal.mjs';
import {chooseCpuChallenger} from './match-flow.mjs';

const field={x:0,y:0,w:200,h:100,goalH:40};
const keeper=(team,x)=>({team,x,y:50,roster:{position:'GK'}});

test('online keeper catches or parries a shot before the goal line',()=>{
 for(const [team,x,start,end] of [[0,32,50,20],[1,168,150,180]]){
  const goalie=keeper(team,x),ball={x:end,y:50,z:-2,vx:5,vy:0,vz:0,owner:null,actionKind:'shot'};
  const result=resolveOnlineGoalkeeperShot({x:start,y:50,z:-2},ball,[goalie],field,1-team);
  assert.equal(result.kind,'catch');assert.equal(result.team,team);assert.equal(ball.owner,goalie);
 }
 const goalie=keeper(1,168),ball={x:180,y:65,z:-15,vx:7,vy:0,vz:0,owner:null,actionKind:'shot'};
 const result=resolveOnlineGoalkeeperShot({x:150,y:65,z:-15},ball,[goalie],field,0);
 assert.equal(result.kind,'parry');assert.equal(result.team,1);assert.equal(ball.owner,null);
});

test('a rising shot is intercepted at the first reachable point on either side',()=>{
 for(const [team,x,start,end] of [[0,32,50,20],[1,168,150,180]]){
  const goalie=keeper(team,x),ball={x:end,y:50,z:-30,vx:team?-5:5,vy:0,vz:-29,owner:null,actionKind:'shot'};
  const contact=goalkeeperShotContact({x:start,y:50,z:-1},ball,[goalie],field,1-team);
  assert.ok(contact);assert.ok(Math.abs(contact.t-1/6)<1e-12);assert.ok(contact.z>=-21);
  assert.ok(resolveOnlineGoalkeeperShot({x:start,y:50,z:-1},ball,[goalie],field,1-team));
 }
});

test('a caught ball remains with the keeper and cannot be stolen as a ground dribble',()=>{
 const goalie=keeper(1,168),opponent={team:0,x:168,y:50};
 const ball={x:180,y:50,z:-1,vx:5,vy:0,vz:0,owner:null,actionKind:'shot'};
 assert.equal(resolveOnlineGoalkeeperShot({x:150,y:50,z:-1},ball,[goalie],field,0).kind,'catch');
 assert.equal(ball.keeperHeld,true);
 assert.equal(canStealBall(opponent,ball,2000,0),false);
 assert.equal(chooseCpuChallenger([opponent],null,ball,2000,0),null);
 goalie.x=160;advanceOnlineBall(ball,[opponent],1,1,2000);
 assert.equal(ball.owner,goalie);assert.equal(ball.x,goalie.x);assert.equal(ball.y,goalie.y);
 ball.owner=null;assert.equal(settleHeldGoalkeeperBall(ball),false);assert.equal(ball.keeperHeld,false,'stale caught state clears without a keeper');
});

test('the provisional goalkeeper pass flies, bounces and slows after release',()=>{
 for(const sign of [-1,1]){
  const goalie=keeper(sign>0?0:1,100),ball={owner:goalie,keeperHeld:true,x:100,y:50,z:0};
  releaseHeldGoalkeeperPass(ball,goalie,{x:sign,y:0},2.5);
  assert.equal(ball.owner,null);assert.equal(ball.keeperHeld,false);assert.equal(ball.actionKind,'keeper_throw');
  assert.equal(Math.sign(ball.vx),sign);let airborne=false,bounced=false,previousVz=ball.vz;
  for(let tick=0;tick<300;tick++){
   advanceOnlineBall(ball,[],1,goalie.team,1000);
   if(ball.z<0)airborne=true;
   if(previousVz>0&&ball.vz<0)bounced=true;
   previousVz=ball.vz;
  }
  assert.ok(airborne);assert.ok(bounced);assert.equal(ball.z,0);assert.equal(ball.vz,0);assert.equal(Math.abs(ball.vx),0);
 }
});

test('a goal line crossing before the keeper still scores',()=>{
 const goalie=keeper(1,220),ball={x:230,y:50,z:-1,vx:40,vy:0,vz:0,owner:null,actionKind:'shot'};
 const previous={x:190,y:50,z:-1};
 assert.equal(resolveOnlineGoalkeeperShot(previous,ball,[goalie],field,0),null);
 let scored=null;const event=resolveOnlineFieldExit(previous,ball,field,0,{goal:team=>{scored=team;},restart:()=>{}});
 assert.equal(event.type,'goal');assert.equal(scored,0);
});

test('a goalkeeper contact at the same instant as the line wins like local play',()=>{
 const goalie=keeper(1,217.7),ball={x:230,y:50,z:-1,vx:5,vy:0,vz:0,owner:null,actionKind:'shot'},previous={x:190,y:50,z:-1};
 assert.equal(goalkeeperShotContact(previous,ball,[goalie],field,0).t,classifyFieldExitWithTime(previous,ball,field,0).time);
 const save=resolveOnlineGoalkeeperShot(previous,ball,[goalie],field,0);
 assert.equal(save.kind,'catch');assert.equal(ball.owner,goalie);
});

test('shot save runs before a nearby human pickup and preserves keeper possession',()=>{
 const goalie=keeper(1,168),human={team:0,x:175,y:50,vx:0,vy:0};
 const ball={x:150,y:50,z:0,vx:25,vy:0,vz:0,gravity:.14,owner:null,actionKind:'shot'};
 let saved=null;
 const last=advanceOnlineBall(ball,[human],1,0,1000,undefined,field,(previous,current,team)=>{
  saved=resolveOnlineGoalkeeperShot(previous,current,[goalie],field,team);return saved;
 });
 assert.equal(saved.kind,'parry');assert.equal(last,1);assert.equal(ball.owner,null);
});

test('a goalkeeper parry continues airborne without premature ground pickup',()=>{
 const goalie=keeper(1,168),human={team:0,x:168,y:65,vx:0,vy:0};
 const ball={x:150,y:65,z:-15,vx:7,vy:0,vz:0,gravity:.14,owner:null,actionKind:'shot'};
 let saved=null;
 advanceOnlineBall(ball,[],3,0,1000,undefined,field,(previous,current,team)=>{
  saved=resolveOnlineGoalkeeperShot(previous,current,[goalie],field,team);return saved;
 });
 assert.equal(saved.kind,'parry');
 const height=ball.z,velocity=ball.vz,speed=Math.hypot(ball.vx,ball.vy);
 advanceOnlineBall(ball,[human],1,1,1000,undefined,field);
 assert.ok(ball.z<height);assert.ok(ball.vz>velocity);
 assert.equal(Math.hypot(ball.vx,ball.vy),speed);assert.equal(ball.owner,null);
});
