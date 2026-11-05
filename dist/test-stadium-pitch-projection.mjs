import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {projectPitchToSource,unprojectSourceToPitch} from './stadium-pitch-projection.mjs';
const observation=JSON.parse(readFileSync(new URL('../docs/issd-stadium-projection-observation.json',import.meta.url),'utf8'));
const field={x:65,y:52,w:1150,h:523};
for(const [x,y,label] of [[field.x,field.y,'top_left'],[field.x+field.w,field.y,'top_right'],[field.x,field.y+field.h,'bottom_left'],[field.x+field.w,field.y+field.h,'bottom_right']]){
 const p=projectPitchToSource(x,y,field);assert.deepEqual([p.x,p.y],observation.corners[label]);
 const inverse=unprojectSourceToPitch(p.x,p.y,field);assert.ok(Math.abs(inverse.x-x)<1e-9&&Math.abs(inverse.y-y)<1e-9);
}
for(const [x,y] of [[300,90],[640,300],[1150,550]]){const p=projectPitchToSource(x,y,field),q=unprojectSourceToPitch(p.x,p.y,field);assert.ok(Math.abs(q.x-x)<1e-9&&Math.abs(q.y-y)<1e-9);}
assert.throws(()=>projectPitchToSource(0,0,{...field,w:0}),RangeError);
console.log('OK: projeção e inversa correspondem às linhas medidas do layout 1');
