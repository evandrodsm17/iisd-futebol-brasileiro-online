import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {inputAxes} from './input-frame.mjs';
import {planShot} from './shot-model.mjs';
import {passDirection} from './pass-direction.mjs';
const source=readFileSync(new URL('./game.js',import.meta.url),'utf8');
const shoot=source.match(/^function shoot\(actor,input\) \{.*\}$/m)?.[0];
const pass=source.match(/^function pass\(actor,input\) \{.*\}$/m)?.[0];
const input={up:false,down:false,left:true,right:false,run:false,actions:[]};
test('shoot and pass use the requested actor on either team',()=>{
 assert.ok(shoot);assert.ok(pass);
 for(const team of [0,1]){
  const actor={team,x:0,y:0,facingDirection:6},other={team:1-team},ball={owner:actor,x:0,y:0};
  const context={actor,controlled:other,ball,input,inputAxes,planShot,passDirection,Math,simulationNow:()=>100,resetAt:0,players:[actor],isFallen:()=>false,simulationTick:0,screenToWorldVector:(_actor,x,y)=>({x,y}),choosePassTarget:()=>null,planGroundPass:(_ball,direction)=>({direction,speed:2.5}),launched:null};
  context.launchShot=(p,_aim,plan)=>{context.launched={p,plan};};
  vm.runInNewContext(`${shoot};shoot(actor,input);`,context);assert.equal(context.launched.p,actor);assert.ok(context.launched.plan.vx<0);
  context.launched=null;context.launchPass=(p,direction,speed)=>{context.launched={p,direction,speed};};
  vm.runInNewContext(`${pass};pass(actor,input);`,context);assert.equal(context.launched.p,actor);assert.ok(context.launched.direction.x<0);
  ball.owner=other;context.launched=null;vm.runInNewContext(`${shoot};shoot(actor,input);${pass};pass(actor,input);`,context);assert.equal(context.launched,null);
 }
});
