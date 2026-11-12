import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolveNativeMovementAttributes as resolve} from './native-movement-attributes.mjs';
import {candidateMovementAttributeFields as nativeFields} from '../tools/native_movement_progression.mjs';
import {emptyOverrides,updateRomPlayer,applyRomOverrides} from './editor/rom-overrides.mjs';

const catalog=JSON.parse(readFileSync(new URL('./data/issd-rom-catalog.json',import.meta.url),'utf8'));
let checked=0;
for(const team of catalog.teams)for(const player of team.players){
  const byte=parseInt(player.raw.attributes_hex.slice(0,2),16);
  for(let state=0;state<=4;state++){
    const result=resolve(player,state),expected=nativeFields(byte,state);
    assert.equal(result.effectiveByte,byte);
    assert.deepEqual(result.edited,{acceleration:false,speed:false});
    assert.deepEqual({limitLow:result.limitLow,delayLow:result.delayLow},expected);
  }
  checked++;
}
assert.equal(checked,720);
const original=catalog.teams[2].players[9];
const values={...original,target_team_id:2,attributes:{...original.attributes,speed:1,acceleration:99}};
const overrides=updateRomPlayer(emptyOverrides(),2,9,values,original);
const edited=applyRomOverrides(catalog,overrides).teams[2].players[9];
const result=resolve(edited,3);
assert.equal(edited.raw.attributes_hex,original.raw.attributes_hex);
assert.equal(result.originalByte,0x67);
assert.equal(result.effectiveByte,0x92);
assert.deepEqual(result.edited,{acceleration:true,speed:true});
assert.deepEqual({limitLow:result.limitLow,delayLow:result.delayLow},{limitLow:2,delayLow:0});
const speedOnly=resolve({...original,attributes:{...original.attributes,speed:1}},3);
assert.equal(speedOnly.effectiveByte,0x62);
assert.deepEqual(speedOnly.edited,{acceleration:false,speed:true});
const lowNative={...original,raw:{...original.raw,attributes_hex:'01767775670900'},attributes:{...original.attributes,acceleration:3,speed:3}};
assert.equal(resolve(lowNative,3).effectiveByte,0x01,'native nibbles 0 and 1 survive untouched');
const highNative={...original,raw:{...original.raw,attributes_hex:'a7767775670900'},attributes:{...original.attributes,acceleration:95}};
assert.throws(()=>resolve(highNative,3),RangeError);
assert.equal(resolve({attributes:original.attributes},3),null);
assert.throws(()=>resolve(original,5),RangeError);
assert.throws(()=>resolve({...original,attributes:{...original.attributes,speed:100}},3),RangeError);
console.log('OK: 720 registros, estados nativos e edições sem alterar os bytes originais');
