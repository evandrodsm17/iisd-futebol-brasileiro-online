import assert from 'node:assert/strict';
import {createPitchView} from './pitch-view.mjs';
const field={x:65,y:52,w:1150,h:523},crop={x:48,y:80,w:2688,h:848};
for(const layout of [0,1,2,3,4,5,6,7]){
 const view=createPitchView({enabled:true,layout,field,crop,imageReady:true}),at={x:600,y:300};
 assert.equal(view.active,true);
 for(const [x,y] of [[1,0],[0,1],[-1,0],[0,-1],[1,1],[-1,1],[-1,-1],[1,-1]]){
  const world=view.input(x,y,at),shown=view.vector(world.x,world.y,at),cross=shown.x*y-shown.y*x;
  assert.ok(Math.abs(cross)<0.001,`layout ${layout}: controle deve seguir direção da tela`);
  assert.ok(shown.x*x+shown.y*y>0);
 }
}
for(const values of [{enabled:false,layout:1,imageReady:true},{enabled:true,layout:'custom:1',imageReady:true},{enabled:true,layout:1,imageReady:false}]){
 const view=createPitchView({...values,field,crop});assert.equal(view.active,false);assert.deepEqual(view.point(10,20),{x:10,y:20});assert.deepEqual(view.input(0,1,{x:10,y:20}),{x:0,y:1});
}
console.log('OK: projeção visual, direções e reserva para imagens não medidas');
