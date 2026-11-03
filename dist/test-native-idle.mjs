import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {createIdleRenderer} from './native-idle.mjs';
import {previewPixels} from './editor/rom-player-preview.mjs';
const path=new URL('./assets/issd/editor-preview-local.json',import.meta.url);
if(existsSync(path)){
 const data=JSON.parse(readFileSync(path,'utf8')),palette=Array(16).fill('#228844');let image;
 const makeCanvas=(width,height)=>({width,height,getContext:()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:value=>{image=value;}})});
 const renderer=createIdleRenderer(data,makeCanvas),map=[6,7,0,1,2,3,4,5];
 for(let direction=0;direction<8;direction++){
  const request={team:2,kit:'home',direction,palette,appearance:{skin_tone:0,hair_style:1},position:'MF'};
  const canvas=renderer.frame(request),expected=previewPixels(data,2,map[direction],'MF',0,1);
  assert.equal(canvas.width,48);assert.equal(canvas.height,56);
  for(let i=0;i<expected.pixels.length;i++)assert.equal(image.data[i*4+3],expected.pixels[i]&&expected.pixels[i]!==15?255:0,`direction ${direction}, pixel ${i}`);
  assert.equal(renderer.frame(request),canvas);
 }
 assert.equal(renderer.frame({team:2,kit:'home',direction:8,palette}),null);
 console.log('OK: oito poses do editor reproduzem a máscara original, com cabelo');
}else console.log('OK: dados locais do editor indisponíveis');
