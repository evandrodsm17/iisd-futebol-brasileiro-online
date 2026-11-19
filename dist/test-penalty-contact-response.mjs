import test from 'node:test';
import assert from 'node:assert/strict';
import {nativePenaltyContactResponse as respond} from './penalty-contact-response.mjs';

test('native response preserves fractional Y and wraps horizontal addition',()=>{
 const value={target:{y:0x123456,vx:0xfffffe,vy:9,vz:2},peerY:0xffff,source:{vx:5,vz:0}};
 assert.deepEqual(respond(value),{y:0x000356,vx:3,vy:0,vz:0xffffff});
 assert.equal(value.target.vy,9);
 assert.throws(()=>respond({...value,peerY:-1}),RangeError);
});

test('carry from the rotate remains active through the byte increment',()=>{
 const target={y:0,vx:0,vy:0,vz:3},source={vx:0,vz:0};
 assert.equal(respond({target,source,peerY:0}).vz,0x0000ff);
});

import {readFileSync} from 'node:fs';
test('matches the two captured object-contact responses',()=>{
 const report=JSON.parse(readFileSync(new URL('../docs/issd-penalty-contact-response.json',import.meta.url),'utf8'));
 assert.equal(report.cases.length,2);
 for(const sample of report.cases){
  const a=sample.input;
  const result=respond({target:{y:a.target_y,vx:a.target_vx,vy:a.target_vy,vz:a.target_vz},peerY:a.peer_y,source:{vx:a.source_vx,vz:a.source_vz}});
  assert.deepEqual(result,{y:sample.output.target_y,vx:sample.output.target_vx,vy:sample.output.target_vy,vz:sample.output.target_vz});
  assert.equal(result.vz,325);
 }
});
