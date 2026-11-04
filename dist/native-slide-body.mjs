import {composeOam} from './native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// One observed body-only sequence: Brazil/home, light skin, ROM direction 0.
// The defensive contact behavior remains the separately provisional web logic.
export function createNativeSlideBody(data,locomotion,makeCanvas){
 if(data?.schema!=='issd-slide-lab-local/v1'||data.width!==96||data.height!==96||!Array.isArray(data.frames)||data.frames.length!==6||locomotion?.schema!=='issd-runtime-body-local/v1')throw Error('Dados locais de carrinho incompatíveis');
 const referenceHeight=locomotion.cycles?.walking?.[0]?.height;
 if(!Number.isInteger(referenceHeight)||referenceHeight<1||referenceHeight>256)throw Error('Escala de carrinho indisponível');
 const duration=data.frames.reduce((sum,f)=>{if(!Number.isInteger(f.ticks)||f.ticks<1||!Array.isArray(f.tiles)||!Array.isArray(f.parts))throw Error('Quadro de carrinho inválido');return sum+f.ticks;},0),cache=new Map();
 return {
  duration,referenceHeight,
  supports({team,kit,appearance,position,screenDirection}){return team===30&&kit==='home'&&position!=='GK'&&appearance?.skin_tone===0&&Number.isInteger(appearance?.hair_style)&&appearance.hair_style>=0&&appearance.hair_style<=13&&screenDirection===2;},
  frame(ticks){
   if(!Number.isFinite(ticks)||ticks<0||ticks>=duration)return null;
   let remaining=Math.floor(ticks),index=0;while(remaining>=data.frames[index].ticks){remaining-=data.frames[index].ticks;index++;}
   if(cache.has(index))return cache.get(index);
   const f=data.frames[index],vram=new Uint8Array(65536);
   for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>vram.length)throw Error('Tile de carrinho inválido');vram.set(bytes,tile.address);}
   const result=composeOam({vram,cgram:decode(f.cgram),obsel:f.obsel,parts:f.parts,width:96,height:96});
   const canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),image=ctx.createImageData(96,96);image.data.set(result.rgba);ctx.putImageData(image,0,0);cache.set(index,canvas);return canvas;
  }
 };
}
export async function loadNativeSlideBody(){
 const [r,m]=await Promise.all([fetch('./assets/issd/slide-lab-local/preview.json'),fetch('./assets/issd/runtime-body-local.json')]);
 if(!r.ok||!m.ok)throw Error('Dados locais de carrinho indisponíveis');
 return createNativeSlideBody(await r.json(),await m.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
