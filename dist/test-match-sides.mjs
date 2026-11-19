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

test('formation homes mirror horizontally while preserving role and width',async()=>{
 const {runInNewContext}=await import('node:vm');
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const formation=source.match(/function formationHome\(team, side, playerIndex\) \{[\s\S]*?\n\}/);
 assert.ok(formation);
 for(const side of [0,1])for(const playerIndex of [0,1]){
  const context={teamDefendsLeft,field:{x:50,y:10,w:1000,h:500},fieldMidX:550,fieldMidY:260,formationRoleDepth:{DF:1},formationProjection:{depth:20,width:10},catalog:null};
  const call=`${formation[0]};formationHome({formation:{outfield_slots:[{role_code:'DF',depth:2,width:3}]}},${side},${playerIndex})`;
  const initial=runInNewContext(call,context);
  context.field={...context.field,teamsSwapped:true};
  const swapped=runInNewContext(call,context);
  assert.equal(swapped.x,mirrorFieldX(initial.x,context.field));
  assert.equal(swapped.y,initial.y);assert.equal(swapped.role,initial.role);
 }
});

test('kickoff faces the current attacking direction for both teams',async()=>{
 const {runInNewContext}=await import('node:vm');
 const {ballFootTarget}=await import('./dribble-contact.mjs');
 const {chooseControlledNearBall}=await import('./match-flow.mjs');
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const reset=source.match(/^function reset\(kickoffTeam=0\) \{.*\}$/m);assert.ok(reset);
 for(const swapped of [false,true])for(const kickoff of [0,1]){
  const result=runInNewContext(`(()=>{const field={x:0,y:0,w:200,h:100,teamsSwapped:swapped},fieldMidX=100,fieldMidY=50,players=[{team:0,homeX:40,homeY:40},{team:1,homeX:160,homeY:60}],player=players[0];let controlled=player,humanAssignments=new Map([[0,players[0]],[1,players[1]]]),ball={},trackedOwner,lastTouchTeam,resetAt,simulationTick=0;const snapCameraToBall=()=>{},simulationNow=()=>0;${reset[0]};reset(kickoff);return {players,ball};})()`,{swapped,kickoff,teamDefendsLeft,ballFootTarget,chooseControlledNearBall});
  assert.equal(result.players[0].facingDirection,swapped?6:2);
  assert.equal(result.players[1].facingDirection,swapped?2:6);
  assert.equal(result.ball.owner.team,kickoff);assert.equal(result.ball.x,100);assert.equal(result.ball.y,50);
 }
});

test('first period expires once, preserves score and resets the second clock',async()=>{
 const {runInNewContext}=await import('node:vm');
 const {decrementMatchBcd}=await import('./match-clock.mjs');
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const advance=source.match(/function advanceMatchClock\(dt\) \{[\s\S]*?\n\}/);
 const second=source.match(/function startSecondHalf\(\) \{[\s\S]*?\n\}/);
 assert.ok(advance&&second);
 const result=runInNewContext(`(()=>{let matchClockBcd=1,matchClockFrames=59,matchPeriod=0,score=[2,1],field={},called=[],toast={classList:{add(){},remove(){}}};const rosterTeam=n=>n,applyFormation=(team,side)=>called.push([team,side]),initializeMatchClock=()=>{matchClockBcd=0x0500;matchClockFrames=0;},reset=team=>called.push(team),renderClock=()=>{},setTimeout=()=>{};${advance[0]};${second[0]};const changed=advanceMatchClock(1/60);return {changed,matchClockBcd,matchPeriod,score,field,called};})()`,{decrementMatchBcd});
 assert.equal(result.changed,true);assert.equal(result.matchPeriod,1);assert.equal(result.matchClockBcd,0x0500);
 assert.deepEqual([...result.score],[2,1]);assert.equal(result.field.teamsSwapped,true);
 assert.deepEqual(JSON.parse(JSON.stringify(result.called)),[[0,0],[1,1],1]);
});

test('regulation ending preserves the score and tells the player when a draw is unresolved',async()=>{
 const {runInNewContext}=await import('node:vm');
 const {decrementMatchBcd}=await import('./match-clock.mjs');
 const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
 const advance=source.match(/function advanceMatchClock\(dt\) \{[\s\S]*?\n\}/);
 const finish=source.match(/function finishRegulation\(\) \{[\s\S]*?\n\}/);
 assert.ok(advance&&finish);
 for(const values of [[2,1],[1,1]]){
  const result=runInNewContext(`(()=>{let matchClockBcd=1,matchClockFrames=59,matchPeriod=1,matchFinished=false,score=[...values],players=[{vx:2,vy:3}],ball={vx:1,vy:2,vz:-1},note={};const document={querySelector:()=>note},actionQueue={clear(){}},renderClock=()=>{};${advance[0]};${finish[0]};const changed=advanceMatchClock(1/60);return {changed,matchFinished,matchClockBcd,score,players,ball,note};})()`,{values,decrementMatchBcd});
  assert.equal(result.changed,true);assert.equal(result.matchFinished,true);assert.equal(result.matchClockBcd,0);
  assert.deepEqual([...result.score],values);assert.equal(result.players[0].vx,0);assert.equal(result.ball.vx,0);
  assert.match(result.note.textContent,values[0]===values[1]?/EMPATE.*PRORROGAÇÃO/:/RESULTADO FINAL/);
 }
});
