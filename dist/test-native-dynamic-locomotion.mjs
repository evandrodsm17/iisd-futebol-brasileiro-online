import assert from 'node:assert/strict';
import {createDynamicLocomotion} from './native-dynamic-locomotion.mjs';

const calls=[];
function makeCanvas(width,height){
 const ctx={drawImage:(...args)=>calls.push(args),createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),
  getImageData:()=>({data:new Uint8ClampedArray(width*height*4)}),putImageData:()=>{}};
 return {width,height,getContext:()=>ctx};
}
const hair=btoa(String.fromCharCode(...Array(64).fill(1)));
const audit={schema:'issd-dynamic-hair-audit/v1',team:2,kit:'home',motion:'walking',direction:4,style:1,cell_width:34,cell_height:52,
 palette_rgb:[[0,0,0],[1,2,3]],frames:[{sheet_frame:3,origin_x:10,origin_y:20,hair_x:1,hair_y:-8,selector:1}]};
const renderer=createDynamicLocomotion({audit,atlas:{schema:'issd-editor-preview-local/v1',hair_tiles:Array.from({length:13},()=>[hair])},details:{tiles:{}},colors:{},image:{},makeCanvas});
const request={team:2,kit:'home',motion:'walking',direction:4,appearance:{hair_style:1,skin_tone:0},position:'MF',frame:3};
const composed=renderer.frame(request);
assert.equal(composed.width,34);assert.equal(calls.length,2);
assert.equal(renderer.frame(request),composed);assert.equal(calls.length,2,'cached frame');
for(const style of [2,13]){
 const variant=renderer.frame({...request,appearance:{hair_style:style,skin_tone:0}});
 assert.notEqual(variant,composed);assert.equal(renderer.frame({...request,appearance:{hair_style:style,skin_tone:0}}),variant);
}
for(const change of [{team:3},{kit:'away'},{motion:'running'},{direction:0},{appearance:{hair_style:3,skin_tone:0}},{appearance:{hair_style:1,skin_tone:1}},{position:'GK'},{frame:0}])assert.equal(renderer.frame({...request,...change}),null);
console.log('OK: composição limitada aos quadros e aparência observados');
