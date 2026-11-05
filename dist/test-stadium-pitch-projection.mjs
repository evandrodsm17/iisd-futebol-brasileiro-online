import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {projectPitchToSource,unprojectSourceToPitch,projectPitchToCanvas,unprojectCanvasToPitch,canvasDirectionToPitch} from './stadium-pitch-projection.mjs';
const observation=JSON.parse(readFileSync(new URL('../docs/issd-stadium-projection-observation.json',import.meta.url),'utf8'));
const observations=JSON.parse(readFileSync(new URL('../docs/issd-stadium-projections-observation.json',import.meta.url),'utf8'));
const field={x:65,y:52,w:1150,h:523};
for(const [x,y,label] of [[field.x,field.y,'top_left'],[field.x+field.w,field.y,'top_right'],[field.x,field.y+field.h,'bottom_left'],[field.x+field.w,field.y+field.h,'bottom_right']]){
 const p=projectPitchToSource(x,y,field);assert.deepEqual([p.x,p.y],observation.corners[label]);
 const inverse=unprojectSourceToPitch(p.x,p.y,field);assert.ok(Math.abs(inverse.x-x)<1e-9&&Math.abs(inverse.y-y)<1e-9);
}
for(const [x,y] of [[300,90],[640,300],[1150,550]]){const p=projectPitchToSource(x,y,field),q=unprojectSourceToPitch(p.x,p.y,field);assert.ok(Math.abs(q.x-x)<1e-9&&Math.abs(q.y-y)<1e-9);}
for(const layout of [0,1,3]){
 const expected=observations.layouts.find(r=>r.layout===layout);assert.equal(expected.status,'measured');
 for(const [x,y,label] of [[field.x,field.y,'top_left'],[field.x+field.w,field.y,'top_right'],[field.x,field.y+field.h,'bottom_left'],[field.x+field.w,field.y+field.h,'bottom_right']]){
  const p=projectPitchToSource(x,y,field,layout);assert.deepEqual([p.x,p.y],expected.observation.corners[label]);
  const inverse=unprojectSourceToPitch(p.x,p.y,field,layout);assert.ok(Math.abs(inverse.x-x)<1e-9&&Math.abs(inverse.y-y)<1e-9);
 }
}
assert.throws(()=>projectPitchToSource(0,0,field,2),RangeError,'estádios não medidos não recebem projeção inventada');
const layouts=JSON.parse(readFileSync(new URL('./data/issd-stadium-layouts.json',import.meta.url),'utf8')).layouts;
for(const layout of [0,1,3]){
 const crop=layouts.find(r=>r.id===layout).crop;
 for(const [x,y] of [[field.x,field.y],[640,300],[field.x+field.w,field.y+field.h]]){
  const projected=projectPitchToCanvas(x,y,field,crop,layout),back=unprojectCanvasToPitch(projected.x,projected.y,field,crop,layout);
  assert.ok(Math.abs(back.x-x)<1e-9&&Math.abs(back.y-y)<1e-9);
 }
 const direction=canvasDirectionToPitch(0,1,field,crop,layout),a=projectPitchToCanvas(600,300,field,crop,layout),b=projectPitchToCanvas(600+direction.x,300+direction.y,field,crop,layout);
 assert.ok(Math.abs(b.x-a.x)<1e-9&&Math.abs((b.y-a.y)-1)<1e-9,'entrada vertical permanece vertical na tela');
}
assert.throws(()=>projectPitchToSource(0,0,{...field,w:0}),RangeError);
console.log('OK: projeção e inversa correspondem às linhas medidas do layout 1');
