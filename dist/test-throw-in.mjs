import test from 'node:test';
import assert from 'node:assert/strict';
import {beginThrowIn,advanceThrowIn} from './throw-in.mjs';
const empty={up:false,down:false,left:false,right:false,run:false,actions:[]},world=(_p,x,y)=>({x,y});
test('human aims, holds the ball and releases into the field',()=>{
 const p={team:1,x:100,y:12,vx:1,vy:1},ball={},state=beginThrowIn(p,{y:0,h:100},ball);
 assert.equal(ball.owner,p);assert.equal(ball.z,-22);assert.equal(state.inward,1);
 assert.equal(advanceThrowIn(state,{...empty,up:true,right:true},true,ball,world),false);
 assert.ok(state.aim.x>0&&state.aim.y>0);assert.equal(p.vx,0);
 advanceThrowIn(state,{...empty,actions:['shot']},true,ball,world);
 for(let i=0;i<3;i++)assert.equal(advanceThrowIn(state,empty,true,ball,world),false);
 assert.equal(advanceThrowIn(state,empty,true,ball,world),true);assert.equal(ball.owner,null);assert.ok(ball.vy>0&&ball.vz<0);
});
test('CPU restarts and lower-side direction enters the field',()=>{
 const p={team:0,x:100,y:88},ball={},state=beginThrowIn(p,{y:0,h:100},ball);
 for(let i=0;i<30;i++)advanceThrowIn(state,empty,false,ball,world);
 for(let i=0;i<3;i++)assert.equal(advanceThrowIn(state,empty,false,ball,world),false);
 assert.equal(advanceThrowIn(state,empty,false,ball,world),true);assert.ok(ball.vy<0);
});

test('upper-side visual follows only individually captured horizontal inputs',()=>{
 const p={team:0,x:100,y:12},ball={},state=beginThrowIn(p,{y:0,h:100},ball);
 assert.equal(state.visualDirection,4);
 advanceThrowIn(state,{...empty,left:true},true,ball,world);assert.equal(state.visualDirection,5);
 advanceThrowIn(state,{...empty,right:true},true,ball,world);assert.equal(state.visualDirection,3);
 advanceThrowIn(state,{...empty,down:true,right:true},true,ball,world);assert.equal(state.visualDirection,4);
});

test('lower-side visual follows individually captured horizontal inputs',()=>{
 const p={team:0,x:100,y:88},ball={},state=beginThrowIn(p,{y:0,h:100},ball);
 assert.equal(state.visualDirection,0);
 advanceThrowIn(state,{...empty,left:true},true,ball,world);assert.equal(state.visualDirection,7);
 advanceThrowIn(state,{...empty,right:true},true,ball,world);assert.equal(state.visualDirection,1);
 advanceThrowIn(state,{...empty,up:true,right:true},true,ball,world);assert.equal(state.visualDirection,0);
});
