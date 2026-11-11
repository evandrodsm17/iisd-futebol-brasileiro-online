import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('./game.js',import.meta.url),'utf8').replace(/\r\n/g,'\n');
const match=source.match(/function cameraTarget\(\) \{[\s\S]*?\n\}(?=\nfunction snapCameraToBall)/);
assert.ok(match);

test('throw camera keeps both touchlines in view for either online seat',()=>{
 for(const side of ['top','bottom'])for(const seat of [1,2]){
  const field={x:65,y:52,w:1150,h:523},viewport={x:0,y:0,w:1280,h:720},zoom=1.58;
  const receiver={x:640,y:side==='top'?field.y+12:field.y+field.h-12};
  const context={field,throwIn:{receiver},onlineTest:{seat},humanAssignments:new Map([[0,{x:100,y:300}],[1,{x:1100,y:300}]]),ball:{x:0,y:0},activeCameraProfile:()=>({viewport,zoom}),pitchView:()=>({point:(x,y)=>({x,y})}),Math};
  const target=vm.runInNewContext(`${match[0]}\ncameraTarget()`,context);
  const screenY=viewport.h/2+(receiver.y-target.y)*zoom;
  assert.ok(screenY>=70&&screenY<=viewport.h-70,`${side}, seat ${seat}: ${screenY}`);
 }
});
