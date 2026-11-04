import {composeOam} from './native-oam-compositor.mjs';
import {teamDetailColor} from './native-team-detail-color.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
const directionToRom=[6,7,0,1,2,3,4,5];

// Geometry and timing are observed; team palettes and detail variants are ROM-derived.
export function createNativeSlideBody(data,locomotion,makeCanvas,preview,left=null,directions=null,detailManifest=null){
 if(data?.schema!=='issd-slide-lab-local/v1'||data.width!==96||data.height!==96||!Array.isArray(data.frames)||data.frames.length!==6||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais de carrinho incompatíveis');
 const duration=data.frames.reduce((sum,f)=>sum+f.ticks,0),cache=new Map();
 const cycles={2:data.frames};if(left)cycles[6]=left.frames;
 if(directions){if(directions.schema!=='issd-slide-directions-local/v1'||directions.width!==96||directions.height!==96||!Array.isArray(directions.detail_pool))throw Error('Direções de carrinho incompatíveis');Object.assign(cycles,directions.cycles);}
 for(const [direction,frames] of Object.entries(cycles)){
  if(!Number.isInteger(+direction)||+direction<0||+direction>7||!Array.isArray(frames)||frames.length!==6||frames.reduce((sum,f)=>sum+f.ticks,0)!==duration||frames.some(f=>!Number.isInteger(f.ticks)||f.ticks<1||!Array.isArray(f.tiles)||!Array.isArray(f.parts)||f.parts.some(p=>![0,4].includes((p.attr>>1)&7))||f.parts.some(p=>((p.attr>>1)&7)===4)&&(!Array.isArray(f.detail_variants)||f.detail_variants.length!==720||!Number.isInteger(f.detail_address))))throw Error('Quadro de carrinho inválido');
 }
 const validWords=p=>Array.isArray(p)&&p.length===16&&p.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);
 const validColors=p=>Array.isArray(p)&&p.length===16&&p.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 function referenceHeight(dir){const h=locomotion.cycles?.walking?.[directionToRom[dir]]?.height;return Number.isInteger(h)&&h>0&&h<=256?h:null;}
 function supports({team,kit,appearance,position,screenDirection,palette,shirtNumber}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||position==='GK'||![0,1].includes(appearance?.skin_tone)||!Number.isInteger(appearance?.hair_style)||appearance.hair_style<0||appearance.hair_style>13||!validColors(palette)||!validWords(preview.teams?.[team]?.palettes?.[appearance.skin_tone])||!cycles[screenDirection]||!referenceHeight(screenDirection))return false;
  const needsDetail=cycles[screenDirection].some(f=>f.detail_variants);
  if(!needsDetail)return true;
  if(!Number.isInteger(shirtNumber)||shirtNumber<1||shirtNumber>20||!detailManifest||!directions)return false;
  try{if(teamDetailColor(detailManifest,team,kit)===null)return false;}catch{return false;}
  return cycles[screenDirection].every(f=>!f.detail_variants||(Number.isInteger(f.detail_variants[team*20+shirtNumber-1])&&typeof directions.detail_pool[f.detail_variants[team*20+shirtNumber-1]]==='string'));
 }
 return {duration,referenceHeight,supports,
  frame(ticks,request){
   if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=duration)return null;
   const frames=cycles[request.screenDirection];let remaining=Math.floor(ticks),index=0;while(remaining>=frames[index].ticks){remaining-=frames[index].ticks;index++;}
   const {team,kit,appearance,palette,shirtNumber}=request,key=JSON.stringify([request.screenDirection,index,team,kit,appearance.skin_tone,palette,shirtNumber]);if(cache.has(key))return cache.get(key);
   const f=frames[index],vram=new Uint8Array(65536);
   for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>vram.length)throw Error('Tile de carrinho inválido');vram.set(bytes,tile.address);}
   const cgram=decode(f.cgram),skin=preview.teams[team].palettes[appearance.skin_tone];if(cgram.length!==512)throw Error('Paleta de carrinho inválida');
   for(let i=0;i<16;i++){let word=skin[i];if(i>=7){const color=palette[i],r=Math.round(parseInt(color.slice(1,3),16)*31/255),g=Math.round(parseInt(color.slice(3,5),16)*31/255),b=Math.round(parseInt(color.slice(5,7),16)*31/255);word=r|(g<<5)|(b<<10);}const address=(128+i)*2;cgram[address]=word&255;cgram[address+1]=word>>8;}
   if(f.detail_variants){const tile=decode(directions.detail_pool[f.detail_variants[team*20+shirtNumber-1]]);if(tile.length!==32||f.detail_address<0||f.detail_address+32>vram.length)throw Error('Detalhe de uniforme inválido');vram.set(tile,f.detail_address);const rgb=teamDetailColor(detailManifest,team,kit),word=rgb.reduce((w,c,i)=>w|(Math.round(c*31/255)<<(5*i)),0),address=(128+4*16+12)*2;cgram[address]=word&255;cgram[address+1]=word>>8;}
   const result=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96}),canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),image=ctx.createImageData(96,96);image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  }
 };
}
export async function loadNativeSlideBody(){
 const [r,m,p,l,d,c]=await Promise.all([fetch('./assets/issd/slide-lab-local/preview.json'),fetch('./assets/issd/runtime-body-local.json'),fetch('./assets/issd/editor-preview-local.json'),fetch('./assets/issd/slide-lab-local/left.json'),fetch('./assets/issd/slide-lab-local/directions.json'),fetch('./data/issd-team-detail-colors.json')]);
 if(!r.ok||!m.ok||!p.ok)throw Error('Dados locais de carrinho indisponíveis');
 return createNativeSlideBody(await r.json(),await m.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},await p.json(),l.ok?await l.json():null,d.ok?await d.json():null,c.ok?await c.json():null);
}
