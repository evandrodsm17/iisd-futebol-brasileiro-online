import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {createDescriptorLocomotion} from './native-descriptor-locomotion.mjs';

const path=new URL('./assets/issd/hair-lab-local/descriptor-bridge-demo-local.json',import.meta.url);
const hairPath=new URL('./assets/issd/hair-lab-local/hair-descriptor-tiles-local.json',import.meta.url);
const palettePath=new URL('./assets/issd/hair-lab-local/match-palette-local.json',import.meta.url);
if(existsSync(path)&&existsSync(hairPath)&&existsSync(palettePath)){
 const data=JSON.parse(readFileSync(path,'utf8')),hair=JSON.parse(readFileSync(hairPath,'utf8')),palette=JSON.parse(readFileSync(palettePath,'utf8')),calls=[];
 const makeCanvas=(width,height)=>({width,height,getContext:()=>({
  createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:()=>{},drawImage:(...args)=>calls.push(args)
 })});
 const renderer=createDescriptorLocomotion(data,hair,palette,makeCanvas);
 const request={team:2,kit:'home',motion:'walking',direction:4,appearance:{hair_style:1,skin_tone:0},position:'MF',frame:0};
 for(let frame=0;frame<10;frame++){
  const cell=renderer.frame({...request,frame});assert.equal(cell.width,34);assert.equal(cell.height,52);
  assert.equal(renderer.frame({...request,frame}),cell);
 }
 assert.equal(calls.length,10);
 for(const style of [2,13])assert.ok(renderer.frame({...request,appearance:{hair_style:style,skin_tone:0}}));
 for(const change of [{team:3},{kit:'away'},{direction:0},{motion:'running'},{appearance:{hair_style:3,skin_tone:0}},{position:'GK'},{frame:10}])assert.equal(renderer.frame({...request,...change}),null);
 console.log('OK: dez quadros recompostos e seletores preservados');
}else console.log('OK: captura local não disponível');
