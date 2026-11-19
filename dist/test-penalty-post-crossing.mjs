import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {nativePenaltyPostCrossing as transition} from './penalty-post-crossing.mjs';
const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-post-crossing.json',import.meta.url),'utf8'));
test('captured goals agree with ROM transition when supplied observed relevant flag',()=>{
 let count=0;
 for(const capture of report.captures)for(const s of capture.samples){
  const [vx,vy]=s.horizontal_before;
  const result=transition({flags:s.next_flags,height:s.height,vx,vy,vz:s.vertical_velocity});
  assert.equal(result.route,'8e25');assert.deepEqual([result.vx,result.vy],s.horizontal_after);assert.equal(result.vz,s.vertical_velocity);count++;
 }
 assert.equal(count,13);
});
test('branch gates preserve speed where the ROM skips the horizontal stop',()=>{
 const s={flags:0x20,height:0,vx:100,vy:0xffff00,vz:0};
 assert.deepEqual(transition(s),{route:'8e30',vx:s.vx,vy:s.vy,vz:s.vz});
 assert.deepEqual(transition({...s,flags:0x820,height:1}),{route:'8e30',vx:s.vx,vy:s.vy,vz:s.vz});
 assert.deepEqual(transition({...s,flags:0,height:1}),{route:'8e25',vx:s.vx,vy:s.vy,vz:s.vz});
 assert.deepEqual(transition({...s,height:1}),{route:'8e25',vx:0,vy:0,vz:s.vz});
 assert.throws(()=>transition({...s,height:-1}),RangeError);
});
