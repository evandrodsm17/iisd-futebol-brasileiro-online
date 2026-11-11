import test from 'node:test';
import assert from 'node:assert/strict';
import {observedThrowInVector} from './native-throwin-vector.mjs';

test('reconstructs six captured native release vectors',()=>{
 const cases=[
  ['A',8,20,64,1,61952,1,61952],['A',13,20,64,0,38208,1,56512],
  ['A',3,20,64,3,56256,1,11008],['A',30,20,64,65533,11072,0,37056],
  ['B',8,15,56,1,46016,1,46016],['B',30,15,56,65533,34264,0,32424]
 ];
 for(const [button,angle,ballType,magnitude,xi,xf,yi,yf] of cases){
  assert.deepEqual(observedThrowInVector(button,angle),{ballType,magnitude,velocityX:{integer:xi,fraction:xf},velocityY:{integer:yi,fraction:yf}});
 }
});
test('does not extrapolate unobserved inputs',()=>{
 for(const [button,angle] of [['B',3],['X',8],['A',9],['A',3.5],[null,8]])assert.equal(observedThrowInVector(button,angle),null);
});
