import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import {goalkeeperFrameIndex,createGoalkeeperLocomotion} from './native-goalkeeper-locomotion.mjs';
import {renderRuntimeBody} from './native-runtime-body.mjs';
const file=new URL('./assets/issd/goalkeeper-locomotion-local.json',import.meta.url),previewFile=new URL('./assets/issd/editor-preview-local.json',import.meta.url),refsFile=new URL('../analysis/goalkeeper-locomotion-hashes.json',import.meta.url);
if(existsSync(file)&&existsSync(previewFile)&&existsSync(refsFile)){
 const data=JSON.parse(readFileSync(file,'utf8')),preview=JSON.parse(readFileSync(previewFile,'utf8')),refs=JSON.parse(readFileSync(refsFile,'utf8'));
 assert.equal(refs.cases.length,366);assert.equal(data.missing.length,3);
 for(const c of refs.cases){
  const palette=preview.teams[c.team].palettes[2+c.skin].map(w=>'#'+[0,5,10].map(s=>Math.round(((w>>s)&31)*255/31).toString(16).padStart(2,'0')).join(''));
  const result=renderRuntimeBody(data.cycles[c.direction],c.frame,palette);
  assert.equal(createHash('sha256').update(result.rgba).digest('hex'),c.sha256,`${c.team}/${c.skin}/${c.direction}/${c.frame}`);
 }
 assert.deepEqual([0,4,7,10,13,17,20,23,26].map(goalkeeperFrameIndex),[0,1,2,3,4,5,6,7,0]);
 const make=(w,h)=>({width:w,height:h,getContext:()=>({createImageData:(x,y)=>({data:new Uint8ClampedArray(x*y*4)}),putImageData:()=>{}})});
 const renderer=createGoalkeeperLocomotion(data,preview,make);
 assert.ok(renderer.frame({team:2,direction:4,appearance:{skin_tone:0},ticks:0}));
 assert.equal(renderer.frame({team:2,direction:4,appearance:{skin_tone:0},ticks:17}),null,'unobserved keeper frame must fall back');
 console.log('OK: 366 quadros de goleiro e fallback para lacunas');
}else console.log('OK: dados locais de goleiro indisponíveis');
