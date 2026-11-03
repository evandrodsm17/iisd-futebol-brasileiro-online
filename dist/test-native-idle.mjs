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
  const visible=[];for(let i=0;i<expected.pixels.length;i++)if(expected.pixels[i]&&expected.pixels[i]!==15)visible.push([i%48,Math.floor(i/48)]);
  const left=Math.min(...visible.map(p=>p[0])),top=Math.min(...visible.map(p=>p[1]));
  assert.equal(canvas.width,Math.max(...visible.map(p=>p[0]))-left+1);
  assert.equal(canvas.height,Math.max(...visible.map(p=>p[1]))-top+3);
  for(const [x,y] of visible)assert.equal(image.data[((y-top)*canvas.width+x-left)*4+3],255,`direction ${direction}, ${x},${y}`);
  for(let x=0;x<canvas.width;x++)assert.equal(image.data[((canvas.height-1)*canvas.width+x)*4+3],0,'blank row below feet');
  assert.equal(renderer.frame(request),canvas);
 }
 assert.equal(renderer.frame({team:2,kit:'home',direction:8,palette}),null);
 console.log('OK: oito poses do editor reproduzem a máscara original, com cabelo');
}else console.log('OK: dados locais do editor indisponíveis');
