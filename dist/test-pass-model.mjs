import assert from 'node:assert/strict';
import {choosePassTarget,planGroundPass,PASS_FRICTION} from './pass-model.mjs';
const actor={team:0,x:0,y:0},ball={x:0,y:0},forward={team:0,x:90,y:10},opposite={team:0,x:-50,y:0},rival={team:1,x:40,y:0};
assert.equal(choosePassTarget([actor,forward,opposite,rival],actor,ball,{x:1,y:0}),forward,'direção favorece companheiro à frente');
assert.equal(choosePassTarget([actor,opposite,rival],actor,ball,{x:1,y:0}),null,'adversário e companheiro atrás não são alvos');
assert.equal(choosePassTarget([actor,forward],actor,ball,{x:0,y:0}),null);
const plan=planGroundPass(ball,{x:1,y:0},forward);
assert.ok(plan.direction.x>0&&plan.direction.y>0,'passe é alinhado à posição do companheiro');
assert.ok(plan.speed<3.6);
const free=planGroundPass(ball,{x:-1,y:0});assert.equal(free.speed,2.5);assert.equal(free.direction.x,-1);
let speed=plan.speed,x=0,y=0,prior=speed;
for(let i=0;i<120&&speed>0;i++){x+=plan.direction.x*speed;y+=plan.direction.y*speed;speed=Math.max(0,speed-PASS_FRICTION);assert.ok(speed<=prior);prior=speed;}
assert.equal(speed,0,'passe perde força e para');assert.ok(Math.hypot(x-forward.x,y-forward.y)<8,'força é adequada à distância do alvo');
assert.throws(()=>planGroundPass(ball,{x:0,y:0}),RangeError);
console.log('OK: alvo na direção, passe livre, atrito e alcance proporcional');
