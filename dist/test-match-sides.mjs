import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {defendingTeamOnSide,teamDefendsLeft,mirrorFieldX} from './match-sides.mjs';
import {classifyFieldExit} from './field-events.mjs';
import {goalkeeperHome,goalkeeperShotContact} from './goalkeeper-model.mjs';
import {onlineOutfieldTarget} from './online-team-ai.mjs';

const field={x:0,y:0,w:200,h:100,goalH:40,teamsSwapped:true};
test('native captured player positions reflect across the field width',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-period-formations.json',import.meta.url)));
 for(const period of report.comparisons)for(const actor of period.positions){
  assert.equal(mirrorFieldX(actor.before_x,{x:0,w:report.field.width}),actor.after_x);
 }
 assert.equal(mirrorFieldX(80,{x:50,w:200}),220);
});
test('swapped side assigns goals and restarts to the correct teams',()=>{
 assert.equal(defendingTeamOnSide('left',field),1);
 assert.equal(teamDefendsLeft(0,field),false);
 const b=(x,y,z=0)=>({x,y,z});
 assert.equal(classifyFieldExit(b(190,50),b(210,50),field,0).team,1);
 assert.equal(classifyFieldExit(b(10,50),b(-10,50),field,1).team,0);
 assert.equal(classifyFieldExit(b(190,10),b(210,10),field,0).type,'corner');
 assert.equal(classifyFieldExit(b(190,10),b(210,10),field,1).team,0);
});
test('swapped goalkeeper and outfield player use their current sides',()=>{
 const keeper={team:1,x:32,y:50,roster:{position:'GK'}};
 assert.equal(goalkeeperHome(keeper,{y:50},field).x,32);
 const ball={x:30,y:50,z:0,vx:-3,vy:0,owner:null,actionKind:'shot'};
 assert.equal(goalkeeperShotContact({x:45,y:50,z:0},ball,[keeper],field,0)?.keeper,keeper);
 const actor={team:0,x:100,y:50,homeX:100,homeY:50};
 assert.equal(onlineOutfieldTarget(actor,[actor],{owner:actor,x:100,y:50},field,0).x,60);
});

test('CPU shooting and passing use attacking direction after side swap',async()=>{
 const {shouldCpuShoot,chooseCpuPassReceiver}=await import('./match-flow.mjs');
 const wide={x:0,y:0,w:1000,h:100,goalH:40,teamsSwapped:true};
 const shooter={team:0,x:100,y:50},ball={owner:shooter,x:100,y:50,z:0};
 assert.equal(shouldCpuShoot(shooter,null,ball,wide,1000,0),true);
 assert.equal(shouldCpuShoot(shooter,null,ball,{...wide,teamsSwapped:false},1000,0),false);
 const carrier={team:0,x:500,y:50},left={team:0,x:400,y:50},right={team:0,x:600,y:50},passBall={owner:carrier,x:500,y:50,z:0};
 assert.equal(chooseCpuPassReceiver([carrier,left,right],carrier,null,passBall,2000,0,0,wide),left);
 assert.equal(chooseCpuPassReceiver([carrier,left,right],carrier,null,passBall,2000,0,0,{...wide,teamsSwapped:false}),right);
});

test('the actual shot launch aims at the current opposing goal',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const launch=source.match(/^function launchShot\(actor,aimAtGoal=false,shotPlan=null\) \{.*\}$/m);
 assert.ok(launch);
 for(const swapped of [false,true]){
  const result=runInNewContext(`(()=>{const field={x:0,y:0,w:1000,teamsSwapped:swapped},fieldMidY=50,actor={team:0,vx:0,vy:0},ball={x:500,y:50};let lastTouchTeam,lastKick;const simulationNow=()=>1,startActionVisual=()=>{};${launch[0]};launchShot(actor,true);return ball.vx;})()`,{swapped,teamDefendsLeft,planCpuShotVertical:()=>({vz:0,gravity:0}),worldToScreenVector:(_p,x,y)=>({x,y}),screenDirectionForVector:()=>2});
  assert.equal(Math.sign(result),swapped?-1:1);
 }
});
