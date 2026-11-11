import test from 'node:test';
import assert from 'node:assert/strict';
import {applyHumanMovement} from './human-movement.mjs';
const input={up:false,down:false,left:false,right:true,run:false,actions:[]};
const identity=(_actor,x,y)=>({x,y});
test('movement works independently for players on either side',()=>{
 const first={team:0,x:0,y:0,vx:0,vy:0},second={team:1,x:0,y:0,vx:0,vy:0};
 for(let i=0;i<20;i++){applyHumanMovement(first,input,1/60,identity);applyHumanMovement(second,input,1/60,identity);}
 assert.ok(first.x>0);assert.equal(first.x,second.x);assert.equal(first.y,second.y);assert.equal(first.vx,second.vx);
});
test('movement follows the supplied projection and cancels opposing directions',()=>{
 const player={team:1,x:0,y:0,vx:0,vy:0};
 applyHumanMovement(player,input,1/60,(_actor,x,y)=>({x:y,y:x}));
 assert.equal(player.x,0);assert.ok(player.y>0);
 const stopped={team:0,x:0,y:0,vx:0,vy:0};applyHumanMovement(stopped,{...input,left:true},1/60,identity);
 assert.equal(stopped.x,0);assert.equal(stopped.y,0);
});
