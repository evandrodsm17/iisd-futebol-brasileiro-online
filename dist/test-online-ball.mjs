import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceOnlineBall} from './online-ball.mjs';
import {ballFootTarget} from './dribble-contact.mjs';

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
