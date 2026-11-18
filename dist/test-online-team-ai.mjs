import test from 'node:test';
import assert from 'node:assert/strict';
import {onlineOutfieldTarget} from './online-team-ai.mjs';
import {assignmentsAfterPickup} from './match-flow.mjs';
import {choosePassTarget,planGroundPass} from './pass-model.mjs';
import {advanceOnlineBall} from './online-ball.mjs';

const field={x:0,y:0,w:200,h:100,goalH:40};
test('uncontrolled outfield players keep shape and closest defender pursues',()=>{
 const a={team:0,x:30,y:40,homeX:30,homeY:40},b={team:0,x:60,y:50,homeX:60,homeY:50},keeper={team:0,x:70,y:50,roster:{position:'GK'}};
 const opponent={team:1,x:90,y:50},players=[a,b,keeper,opponent],ball={x:90,y:50,owner:opponent};
 assert.deepEqual(onlineOutfieldTarget(b,players,ball,field,0),{x:90,y:50,running:true});
 assert.deepEqual(onlineOutfieldTarget(a,players,ball,field,0),{x:30,y:40,running:false});
 ball.owner=a;
 assert.deepEqual(onlineOutfieldTarget(b,players,ball,field,0),{x:95,y:50,running:true});
 b.fallUntil=20;ball.owner=opponent;
 assert.deepEqual(onlineOutfieldTarget(a,players,ball,field,10),{x:90,y:50,running:true});
});

test('a pass to an uncontrolled teammate can be collected and transfers control',()=>{
 const passer={team:0,x:50,y:50,vx:0,vy:0},receiver={team:0,x:90,y:50,vx:0,vy:0};
 const ball={x:50,y:50,z:0,vx:0,vy:0,owner:null,passRolling:true};
 const target=choosePassTarget([passer,receiver],passer,ball,{x:1,y:0});
 assert.equal(target,receiver);
 const plan=planGroundPass(ball,{x:1,y:0},target);ball.vx=plan.direction.x*plan.speed;ball.vy=plan.direction.y*plan.speed;
 let last=0;
 for(let i=0;i<80&&!ball.owner;i++)last=advanceOnlineBall(ball,[passer,receiver],1,last,i*1000/60,undefined,field);
 assert.equal(ball.owner,receiver);
 const assignments=assignmentsAfterPickup(new Map([[0,passer]]),ball.owner);
 assert.equal(assignments.get(0),receiver);
});
