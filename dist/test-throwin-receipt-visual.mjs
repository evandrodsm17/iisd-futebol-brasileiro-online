import test from 'node:test';
import assert from 'node:assert/strict';
import {canShowCapturedReceipt} from './throwin-receipt-visual.mjs';
const actor={facingDirection:5,roster:{position:'MF'}},context={side:'lower',nativeHeight:0xffe9},request={screenDirection:3},renderer={supports:r=>r===request};
test('allows only the captured context with available renderer',()=>{
 assert.equal(canShowCapturedReceipt(actor,context,false,renderer,request),true);
 for(const invalid of [{side:'upper',nativeHeight:0xffe9},{side:'lower',nativeHeight:0xffe8},{side:'lower',nativeHeight:0xffea}])assert.equal(canShowCapturedReceipt(actor,invalid,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,facingDirection:4},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,roster:{position:'GK'}},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt(actor,context,true,renderer,request),false);
 assert.equal(canShowCapturedReceipt(actor,context,false,null,request),false);
 assert.equal(canShowCapturedReceipt({...actor,actionVisual:{}},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,throwVisual:{}},context,false,renderer,request),false);
});
