import {previewPixels} from './editor/rom-player-preview.mjs';

// Editor preview directions mapped to the first D320 descriptor per ROM direction.
const EDITOR_DIRECTION=[6,7,0,1,2,3,4,5];
export function createIdleRenderer(data,makeCanvas){
 if(data?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais de espera incompatíveis');
 const cache=new Map();
 return {frame({team,kit,direction,palette,appearance,position}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||!Number.isInteger(direction)||direction<0||direction>7||!Array.isArray(palette)||palette.length!==16)return null;
  const skin=appearance?.skin_tone??0,hair=appearance?.hair_style??0;
  if(![0,1].includes(skin)||!Number.isInteger(hair)||hair<0||hair>13)return null;
  const key=JSON.stringify([team,kit,direction,skin,hair,position,palette]);if(cache.has(key))return cache.get(key);
  const goalie=position==='GK',pose=previewPixels(data,team,EDITOR_DIRECTION[direction],position,skin,hair);
  const canvas=makeCanvas(48,56),ctx=canvas.getContext('2d'),image=ctx.createImageData(48,56);
  for(let i=0;i<pose.pixels.length;i++){
   // The editor preview includes a green ground shadow at palette index 15;
   // the match already draws its own shadow beneath every player.
   const index=pose.pixels[i];if(!index||index===15)continue;const offset=i*4;
   if(!goalie&&index>=7){const color=palette[index];if(typeof color!=='string'||!/^#[0-9a-f]{6}$/i.test(color))throw Error('Paleta de uniforme inválida');for(let c=0;c<3;c++)image.data[offset+c]=parseInt(color.slice(1+c*2,3+c*2),16);}
   else {const word=pose.palette[index];if(!Number.isInteger(word))throw Error('Paleta de pele inválida');for(let c=0;c<3;c++)image.data[offset+c]=Math.round(((word>>(c*5))&31)*255/31);}
   image.data[offset+3]=255;
  }
  ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadIdleRenderer(){
 const response=await fetch('./assets/issd/editor-preview-local.json');if(!response.ok)throw Error('Dados locais de espera indisponíveis');
 return createIdleRenderer(await response.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
