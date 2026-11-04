import {renderRuntimeBody} from './native-runtime-body.mjs';

// One captured context only. Missing data or any different appearance keeps
// the existing provisional action; the local file is extracted from the ROM.
export function createNativePassBody(data, makeCanvas) {
 if(data?.schema!=='issd-pass-body-local/v1'||data.team!==2||data.kit!=='home'||data.screen_direction!==2||data.skin!==0||data.hair!==0||data.width!==96||data.height!==96||!Array.isArray(data.frames)||data.frames.length!==2||data.ticks?.join(',')!=='2,16'||!Array.isArray(data.palette)||data.palette.length!==16||data.palette.some(w=>!Number.isInteger(w)||w<0||w>0x7fff))throw Error('Dados locais do passe incompatíveis');
 const cache=new Map();
 const palette=data.palette.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
 return {
  supports({team,kit,appearance,position,screenDirection}){return team===data.team&&kit===data.kit&&position!=='GK'&&appearance?.skin_tone===data.skin&&appearance?.hair_style===data.hair&&screenDirection===data.screen_direction;},
  frame(ticks){
   if(!Number.isFinite(ticks)||ticks<0||ticks>=18)return null;
   const index=ticks<2?0:1;if(cache.has(index))return cache.get(index);
   const result=renderRuntimeBody(data,index,palette),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
   image.data.set(result.rgba);ctx.putImageData(image,0,0);cache.set(index,canvas);return canvas;
  },
  duration:18,
 };
}
export async function loadNativePassBody(){
 const response=await fetch('./assets/issd/native-pass-body-local.json');if(!response.ok)throw Error('Dados locais do passe indisponíveis');
 return createNativePassBody(await response.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
