import test from 'node:test';
import assert from 'node:assert/strict';
import {canShowCapturedReceipt,canShowContestedReceipt} from './throwin-receipt-visual.mjs';
const actor={team:1,facingDirection:5,roster:{position:'MF'}},context={side:'lower',power:'pass',sourceTeam:1,nativeHeight:0xffe9},request={screenDirection:3},renderer={supports:r=>r===request};
test('allows only the captured context with available renderer',()=>{
 assert.equal(canShowCapturedReceipt(actor,context,false,renderer,request),true);
 for(const invalid of [{...context,side:'upper'},{...context,nativeHeight:0xffe8},{...context,nativeHeight:0xffea},{...context,power:'shot'},{...context,sourceTeam:0}])assert.equal(canShowCapturedReceipt(actor,invalid,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,facingDirection:4},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,roster:{position:'GK'}},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt(actor,context,true,renderer,request),false);
 assert.equal(canShowCapturedReceipt(actor,context,false,null,request),false);
 assert.equal(canShowCapturedReceipt({...actor,actionVisual:{}},context,false,renderer,request),false);
 assert.equal(canShowCapturedReceipt({...actor,throwVisual:{}},context,false,renderer,request),false);
});

test('contested visual is limited to the observed opposing-player context',()=>{
 const player={team:1,facingDirection:4,roster:{position:'MF'}},ctx={side:'lower',power:'shot',sourceTeam:0,nativeHeight:0xffee};
 assert.equal(canShowContestedReceipt(player,ctx,false,renderer,request),true);
 for(const invalid of [{...ctx,sourceTeam:1},{...ctx,power:'pass'},{...ctx,nativeHeight:0xffe9},{...ctx,side:'upper'}])assert.equal(canShowContestedReceipt(player,invalid,false,renderer,request),false);
 assert.equal(canShowContestedReceipt({...player,facingDirection:5},ctx,false,renderer,request),false);
 assert.equal(canShowContestedReceipt(player,ctx,true,renderer,request),false);
});
