import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

test('audited samples report every observed screen-to-native X difference',()=>{
 const data=JSON.parse(readFileSync(new URL('../docs/issd-penalty-ball-screen-x.json',import.meta.url),'utf8'));
 assert.equal(data.schema,'issd-penalty-ball-screen-x/v1');
 assert.equal(data.captures.length,3);
 const all=data.captures.flatMap(capture=>capture.matches);
 assert.equal(all.length,7);
 const differences={};
 for(const sample of all){
  assert.equal(sample.draw_frame,sample.frame-1);
  assert.equal(sample.matching_pixels,32);
  assert.equal(sample.center_x,sample.oam_x+4);
  assert.equal(sample.center_minus_native_x,sample.center_x-sample.native_x);
  differences[sample.center_minus_native_x]=(differences[sample.center_minus_native_x]??0)+1;
 }
 assert.deepEqual(differences,{'0':6,'2':1});
 assert.ok(all.some(sample=>sample.native_x<100)&&all.some(sample=>sample.native_x>150));
});
