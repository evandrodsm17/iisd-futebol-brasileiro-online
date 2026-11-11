import test from 'node:test';
import assert from 'node:assert/strict';
import {dispatchTeamInputs,moveTeamInputs} from './team-inputs.mjs';
const frame=(right,actions=[])=>({up:false,down:false,left:!right,right,run:false,actions});
test('two team inputs apply in stable order and move separate actors',()=>{
 const a={team:0,x:0,y:0,vx:0,vy:0},b={team:1,x:0,y:0,vx:0,vy:0},actors=new Map([[0,a],[1,b]]),calls=[];
 const handlers={getActor:team=>actors.get(team),shoot:actor=>calls.push(actor.team),pass:()=>{},press:()=>{},switchPlayer:()=>{},reset:()=>{}};
 const inputs=new Map([[1,frame(false,['shot'])],[0,frame(true,['shot'])]]);
 dispatchTeamInputs(inputs,handlers);assert.deepEqual(calls,[0,1]);
 moveTeamInputs(inputs,handlers.getActor,1/60,(_actor,x,y)=>({x,y}));assert.ok(a.x>0);assert.ok(b.x<0);
});
test('absent team input or actor is not fabricated',()=>{
 const player={team:0,x:0,y:0,vx:0,vy:0},actors=new Map([[0,player]]),calls=[];
 const handlers={getActor:team=>actors.get(team),shoot:actor=>calls.push(actor.team),pass:()=>{},press:()=>{},switchPlayer:()=>{},reset:()=>{}};
 dispatchTeamInputs(new Map([[1,frame(true,['shot'])]]),handlers);assert.deepEqual(calls,[]);
 moveTeamInputs(new Map([[1,frame(true)]]),handlers.getActor,1/60,(_actor,x,y)=>({x,y}));assert.equal(player.x,0);
});
