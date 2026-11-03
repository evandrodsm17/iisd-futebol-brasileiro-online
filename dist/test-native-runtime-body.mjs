import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import {renderRuntimeBody} from './native-runtime-body.mjs';
const root=new URL('./assets/issd/runtime-body-local.json',import.meta.url);
const references=new URL('../analysis/runtime-body-hashes.json',import.meta.url);
if(existsSync(root)&&existsSync(references)){
 const data=JSON.parse(readFileSync(root,'utf8')),expected=JSON.parse(readFileSync(references,'utf8'));
 assert.equal(expected.frames.length,864);
 for(const item of expected.frames){
  const result=renderRuntimeBody(data.cycles[item.motion][item.direction],item.frame,item.palette);
  assert.equal(createHash('sha256').update(result.rgba).digest('hex'),item.sha256,`${item.team}/${item.kit}/${item.motion}/${item.direction}/${item.frame}`);
 }
 console.log(`OK: ${expected.frames.length} quadros equivalentes às folhas atuais`);
}else console.log('OK: dados locais ausentes; comparação de folhas ignorada');
