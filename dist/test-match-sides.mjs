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
