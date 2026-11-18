import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceOnlineBall,resolveOnlineFieldExit} from './online-ball.mjs';
import {resolveOnlineGoalkeeperShot} from './online-goalkeeper.mjs';
import {goalkeeperShotContact} from './goalkeeper-model.mjs';
import {classifyFieldExitWithTime} from './field-events.mjs';

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

test('a goal line crossing before the keeper still scores',()=>{
 const goalie=keeper(1,210),ball={x:220,y:50,z:-1,vx:30,vy:0,vz:0,owner:null,actionKind:'shot'};
 const previous={x:190,y:50,z:-1};
 assert.equal(resolveOnlineGoalkeeperShot(previous,ball,[goalie],field,0),null);
 let scored=null;const event=resolveOnlineFieldExit(previous,ball,field,0,{goal:team=>{scored=team;},restart:()=>{}});
 assert.equal(event.type,'goal');assert.equal(scored,0);
});

test('a goalkeeper contact at the same instant as the line wins like local play',()=>{
 const goalie=keeper(1,204.7),ball={x:210,y:50,z:-1,vx:5,vy:0,vz:0,owner:null,actionKind:'shot'},previous={x:190,y:50,z:-1};
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
