import assert from 'node:assert/strict';
import { nativeActionSelection, nativeHeldDirection } from './native-action-selector.mjs';

assert.deepEqual(nativeActionSelection(4,5), {delta:7,field86:0x481,tableOffset:4,control:0xD169,script:0xD16E});
assert.deepEqual(nativeActionSelection(5,3), {delta:2,field86:0x282,tableOffset:2,control:0xD169,script:0xD1C5});
assert.deepEqual(nativeActionSelection(1,1), {delta:0,field86:0,tableOffset:0,control:0xD0F2,script:0xD007});
assert.equal(nativeActionSelection(4,0).field86,0x8004);
assert.equal(nativeActionSelection(4,0).script,null);
assert.deepEqual(Array.from({length:8},(_,i)=>nativeActionSelection(i,0).script),
  [0xD007,0xD1C5,0xD1C5,0xD1C5,null,0xD16E,0xD16E,0xD16E]);
assert.throws(() => nativeActionSelection(-1,0),RangeError);
assert.throws(() => nativeActionSelection(0,0.5),RangeError);
assert.equal(nativeHeldDirection(0x0840),6);
assert.equal(nativeHeldDirection(0x0640),3);
assert.equal(nativeHeldDirection(0x0140),0);
assert.equal(nativeHeldDirection(0x0040),null);
assert.equal(nativeActionSelection(nativeHeldDirection(0x0640),1).script,0xD1C5);
assert.throws(() => nativeHeldDirection(0x10000),RangeError);
console.log('OK: seleção nativa isolada por tabela e comparação angular');
