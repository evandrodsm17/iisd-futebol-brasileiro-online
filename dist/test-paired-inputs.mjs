import test from 'node:test';
import assert from 'node:assert/strict';
import {decodePairedInputs} from './paired-inputs.mjs';
const pair={type:'input-pair-test',epoch:'session',tick:0,inputs:[{tick:0,held:9,actions:['pass']},{tick:0,held:18,actions:['shot']}]};
test('decodes a paired tick to independent team inputs',()=>{
 const decoded=decodePairedInputs(pair,'session',0);assert.deepEqual(decoded.get(0),{up:true,down:false,left:false,right:true,run:false,actions:['pass']});assert.deepEqual(decoded.get(1),{up:false,down:true,left:false,right:false,run:true,actions:['shot']});
 decoded.get(0).actions.push('press');assert.deepEqual(pair.inputs[0].actions,['pass']);
});
test('rejects stale epochs, wrong ticks and malformed pairs',()=>{
 assert.equal(decodePairedInputs(pair,'other',0),null);assert.equal(decodePairedInputs(pair,'session',1),null);
 assert.equal(decodePairedInputs({...pair,inputs:[pair.inputs[0]]},'session',0),null);
 assert.equal(decodePairedInputs({...pair,inputs:[pair.inputs[0],{tick:1,held:0,actions:[]}]},'session',0),null);
 assert.equal(decodePairedInputs({...pair,inputs:[pair.inputs[0],{tick:0,held:32,actions:[]}]},'session',0),null);
 assert.equal(decodePairedInputs({...pair,type:'input-test'},'session',0),null);
});
