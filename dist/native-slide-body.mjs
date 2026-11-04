import {composeOam} from './native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// Body geometry is observed in ROM direction 0. Other palettes are composed
// from the team kit and skin data; the defensive logic remains provisional.
export function createNativeSlideBody(data,locomotion,makeCanvas,preview,left=null){
 if(data?.schema!=='issd-slide-lab-local/v1'||data.width!==96||data.height!==96||!Array.isArray(data.frames)||data.frames.length!==6||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais de carrinho incompatíveis');
 if(left && (left.schema!==data.schema || left.width!==96 || left.height!==96 || !Array.isArray(left.frames) || left.frames.length!==6))throw Error('Dados laterais de carrinho incompat�veis');
 const referenceHeight=locomotion.cycles?.walking?.[0]?.height;
 if(!Number.isInteger(referenceHeight)||referenceHeight<1||referenceHeight>256)throw Error('Escala de carrinho indisponível');
 const duration=data.frames.reduce((sum,f)=>{if(!Number.isInteger(f.ticks)||f.ticks<1||!Array.isArray(f.tiles)||!Array.isArray(f.parts)||f.parts.some(p=>((p.attr>>1)&7)!==0))throw Error('Quadro de carrinho inválido');return sum+f.ticks;},0),cache=new Map();
 if(left && left.frames.some((f,i)=>f.ticks!==data.frames[i].ticks||!Array.isArray(f.tiles)||!Array.isArray(f.parts)||f.parts.some(p=>((p.attr>>1)&7)!==0)))throw Error('Quadros laterais de carrinho incompat�veis');
 const validWords=p=>Array.isArray(p)&&p.length===16&&p.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);
 const validColors=p=>Array.isArray(p)&&p.length===16&&p.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 function supports({team,kit,appearance,position,screenDirection,palette}){return Number.isInteger(team)&&team>=0&&team<36&&['home','away'].includes(kit)&&position!=='GK'&&[0,1].includes(appearance?.skin_tone)&&Number.isInteger(appearance?.hair_style)&&appearance.hair_style>=0&&appearance.hair_style<=13&&(screenDirection===2||(screenDirection===6&&left!==null))&&validColors(palette)&&validWords(preview.teams?.[team]?.palettes?.[appearance.skin_tone]);}
 return {
  duration,referenceHeight,
  supports,
  frame(ticks,request){
   if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=duration)return null;
   let remaining=Math.floor(ticks),index=0;while(remaining>=data.frames[index].ticks){remaining-=data.frames[index].ticks;index++;}
   const {team,kit,appearance,palette}=request,key=JSON.stringify([request.screenDirection,index,team,kit,appearance.skin_tone,palette]);if(cache.has(key))return cache.get(key);
   const f=(request.screenDirection===6?left:data).frames[index],vram=new Uint8Array(65536);
   for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>vram.length)throw Error('Tile de carrinho inválido');vram.set(bytes,tile.address);}
   const cgram=decode(f.cgram),skin=preview.teams[team].palettes[appearance.skin_tone];
   for(let i=0;i<16;i++){let word=skin[i];if(i>=7){const color=palette[i],r=Math.round(parseInt(color.slice(1,3),16)*31/255),g=Math.round(parseInt(color.slice(3,5),16)*31/255),b=Math.round(parseInt(color.slice(5,7),16)*31/255);word=r|(g<<5)|(b<<10);}const address=(128+i)*2;cgram[address]=word&255;cgram[address+1]=word>>8;}
   const result=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96});
   const canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),image=ctx.createImageData(96,96);image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  }
 };
}
export async function loadNativeSlideBody(){
 const [r,m,p,l]=await Promise.all([fetch('./assets/issd/slide-lab-local/preview.json'),fetch('./assets/issd/runtime-body-local.json'),fetch('./assets/issd/editor-preview-local.json'),fetch('./assets/issd/slide-lab-local/left.json')]);
 if(!r.ok||!m.ok||!p.ok)throw Error('Dados locais de carrinho indisponíveis');
 return createNativeSlideBody(await r.json(),await m.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},await p.json(),l.ok?await l.json():null);
}
