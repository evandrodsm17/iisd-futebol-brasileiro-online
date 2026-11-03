import assert from 'node:assert/strict';
import {nativeSlideBallGate} from './native-slide-ball-gate.mjs';
const actor={x:0x4000,y:0x4000,z:0x4000,offsetX:0,offsetY:0,offsetZ:0};
const base={timer:8,actorIsA6:false,actorFlags:0,phase:0,globalFlags:0,priorContactCarry:true,actor,ball:{x:0x4000,y:0x4000,z:0x4000}};
assert.deepEqual(nativeSlideBallGate(base),{route:'contact',timer:7,actorFlags:0x400});
for(const [axis,lo,hi] of [['x',-12,11],['y',-8,7],['z',-8,7]]){
 for(const delta of [lo,hi])assert.equal(nativeSlideBallGate({...base,ball:{...base.ball,[axis]:0x4000+delta}}).route,'contact');
 for(const delta of [lo-1,hi+1])assert.equal(nativeSlideBallGate({...base,ball:{...base.ball,[axis]:0x4000+delta}}).route,'outside');
}
for(const timer of [0,9,12])assert.equal(nativeSlideBallGate({...base,timer}).route,'not_checked');
assert.equal(nativeSlideBallGate({...base,timer:1}).route,'contact');
assert.equal(nativeSlideBallGate({...base,actorIsA6:true}).route,'not_checked');
assert.equal(nativeSlideBallGate({...base,actorFlags:0x20}).route,'not_checked');
assert.equal(nativeSlideBallGate({...base,phase:1}).route,'blocked');
assert.equal(nativeSlideBallGate({...base,globalFlags:0x8000}).route,'blocked');
assert.equal(nativeSlideBallGate({...base,priorContactCarry:false}).route,'prior_response_unresolved');
assert.throws(()=>nativeSlideBallGate({...base,timer:-1}),RangeError);
console.log('OK: janela, guards e limites nativos da verificação do carrinho');
