import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {createPitchView} from './pitch-view.mjs';
import {planShot} from './shot-model.mjs';
import {screenDirectionForVector} from './action-visual.mjs';
import {ballFootTarget} from './dribble-contact.mjs';

const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
const shoot=source.match(/^function shoot\(\) \{.*\}$/m);assert.ok(shoot);
const field={x:65,y:52,w:1150,h:523},crop={x:48,y:80,w:2688,h:848};
for(const layout of [0,1,2,3,4,5,6,7]){
 const view=createPitchView({enabled:true,layout,field,crop,imageReady:true}),actor={team:0,x:600,y:300},ball={owner:actor};
 const result=vm.runInNewContext(`(()=>{const controlled=actor,keys=new Set(['up','run']),bindings={right:'right',left:'left',up:'up',down:'down',run:'run'};let result=null;const simulationNow=()=>100,resetAt=0,launchShot=(p,aim,plan)=>{result=plan;};${shoot[0]};shoot();return result;})()`,{actor,ball,planShot,screenToWorldVector:(p,x,y)=>view.input(x,y,p)});
 const screen=view.vector(result.vx,result.vy,actor);
 assert.ok(screen.x>0&&screen.y<0,`layout ${layout}: chute deve seguir a direção da tela`);
 assert.ok(Math.abs(Math.hypot(result.vx,result.vy)-6.5)<1e-9,'projeção não altera a força');
 const desired=planShot(0,0,-1,true);
 assert.equal(screenDirectionForVector(screen.x,screen.y,2),screenDirectionForVector(desired.vx,desired.vy,2),'animação acompanha direção visível');
}
const stopped={team:0,x:100,y:100,vx:0,vy:0,facingDirection:4,footDirection:[-1,0]};
assert.ok(ballFootTarget(stopped).x<stopped.x,'bola parada usa última orientação no campo, não direção de tela');
const drawBall=source.match(/^function drawBall\(\)\{.*\}$/m);assert.ok(drawBall);
const translations=[],ctx={save(){},restore(){},translate:(...xy)=>translations.push(xy),beginPath(){},ellipse(){},fill(){},arc(){},drawImage(){}};
const renderBall=vm.runInNewContext(`(${drawBall[0]})`,{ctx,Math,ball:{x:50,y:60,z:0},actorVisual:{ball:{shadowX:4,shadowY:2,r:4,patch:1}},ballSprite:{complete:false},BALL_SOURCE_SIZE:12,pitchView:()=>({point:()=>({x:100,y:120})})});
renderBall();assert.deepEqual(translations[0],[100,120],'bola e sombra são posicionadas na projeção medida');
console.log('OK: chute projetado, animação e orientação da bola parada');
