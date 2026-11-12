import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {nativeModeFlagSelection as select} from './native_mode_flag_selection.mjs';

assert.deepEqual(select(4,5,6),{selector:0,field1642:5,field1648:0x00e0});
assert.deepEqual(select(4,4,6),{selector:1,field1642:5,field1648:0x00e0});
assert.deepEqual(select(4,5,4),{selector:2,field1642:5,field1648:0x00e0});
assert.deepEqual(select(4,4,4),{selector:3,field1642:6,field1648:0x0160});
for(const p of [0,1,0x7fff,0xffff])for(const first of [p,(p+1)&0xffff])for(const second of [p,(p+1)&0xffff]){
 const result=select(p,first,second);
 assert.equal(Boolean(result.field1648&0x100),first===p&&second===p);
}
for(const v of [-1,65536,1.5,NaN])assert.throws(()=>select(v,0,0),RangeError);
const path='International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc';
if(existsSync(path)){
 const image=readFileSync(path);
 assert.deepEqual(image.subarray(0x5a1e2,0x5a21c),Buffer.from('22df958ba00000af00dd7ecda00dd001c8af02dd7ecda00dd002c8c8c00300b00ba905008d4216a9e0008009a906008d4216a960018d4816986b','hex'));
}else console.log('ROM local ausente: verificação de opcodes ignorada');
console.log('OK: quatro resultados do seletor e valores gravados');
