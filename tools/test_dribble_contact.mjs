import assert from 'node:assert/strict';
import {ballFootTarget,settleDribble,DRIBBLE} from '../dist/dribble-contact.mjs';
const player={x:490,y:370,vx:2,vy:0,team:0,facingDirection:2};
const ball={x:player.x+12,y:player.y+5,vx:0,vy:0};
for(let i=0;i<60;i++){player.x+=player.vx;const before=ball.x;const state=settleDribble(ball,player,1);assert.ok(ball.x-before<=player.vx+DRIBBLE.maxExtraSpeedPerFrame+1e-9);assert.ok(state.distanceAfter<DRIBBLE.releaseDistance);}
assert.ok(Math.hypot(ball.x-player.x,ball.y-player.y)<13);
player.vx=0;player.vy=0;for(let i=0;i<30;i++)settleDribble(ball,player,1);
assert.ok(Math.hypot(ball.x-ballFootTarget(player).x,ball.y-ballFootTarget(player).y)<.02);
player.facingDirection=6;settleDribble(ball,player,1);
assert.ok(Math.hypot(ball.x-player.x,ball.y-player.y)<DRIBBLE.releaseDistance);
assert.throws(()=>settleDribble(ball,player,-1));
console.log('OK: 60-frame dribble, velocity cap, stopping and turn');
