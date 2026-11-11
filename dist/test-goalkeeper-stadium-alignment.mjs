import test from 'node:test';
import assert from 'node:assert/strict';
import { goalkeeperHome } from './goalkeeper-model.mjs';
import { projectPitchToSource, layout1Pitch } from './stadium-pitch-projection.mjs';
import { createPitchView } from './pitch-view.mjs';
test('goleiros ficam à frente das linhas medidas do estádio, no centro das traves',()=>{
 const field={x:65,y:52,w:1150,h:523,goalH:168},center=field.y+field.h/2;
 const crop={x:48,y:80,w:2688,h:848};
 for(const team of [0,1]){
  const home=goalkeeperHome({team},{y:center},field);
  const pos=projectPitchToSource(home.x,home.y,field,1);
  const lineX=pos.y+(team===0?layout1Pitch.leftXMinusY:layout1Pitch.rightXMinusY);
  const expected=(layout1Pitch.rightXMinusY-layout1Pitch.leftXMinusY)*32/field.w;
  assert.ok(Math.abs((pos.x-lineX)-(team===0?expected:-expected))<1e-9);
  assert.equal(pos.y,(layout1Pitch.topY+layout1Pitch.bottomY)/2);
  const projected=createPitchView({enabled:true,layout:1,field,crop,imageReady:true}).point(home.x,home.y);
  const old={x:home.x,y:home.y};
  assert.ok(Math.hypot(projected.x-old.x,projected.y-old.y)>50,'projeção corrige descompasso da apresentação anterior');
 }
});
