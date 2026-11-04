import {composeOam} from './native-oam-compositor.mjs';
import {teamDetailColor} from './native-team-detail-color.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
const colorsValid=p=>Array.isArray(p)&&p.length===16&&p.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
const wordsValid=p=>Array.isArray(p)&&p.length===16&&p.every(c=>Number.isInteger(c)&&c>=0&&c<=0x7fff);

// Captured OAM geometry and trajectory; team/number variants come from ROM.
// Hair and directions absent from the capture are deliberately not inferred.
export function createNativeCapturedAction(data,preview,detailManifest,makeCanvas,{schema,duration}){
 if(data?.schema!==schema||data.width!==96||data.height!==96||data.ticks_per_second!==60||!Array.isArray(data.detail_pool)||!Array.isArray(data.team_palette)||data.team_palette.length!==36||!Number.isInteger(data.palette10)||data.palette10<0||data.palette10>0x7fff||preview?.schema!=='issd-editor-preview-local/v1'||detailManifest?.schema!=='issd-team-detail-colors/v1')throw Error('Dados dinâmicos da ação incompatíveis');
 const cache=new Map(),tiles=new Map();
 function tileAt(i){if(!Number.isInteger(i)||typeof data.detail_pool[i]!=='string')return null;if(!tiles.has(i)){try{const raw=decode(data.detail_pool[i]);if(raw.length!==32)return null;tiles.set(i,raw);}catch{return null;}}return tiles.get(i);}
 function supports({team,kit,skin,shirtNumber,screenDirection,palette}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||![0,1].includes(skin)||!Number.isInteger(shirtNumber)||shirtNumber<1||shirtNumber>20||!colorsValid(palette)||!wordsValid(preview.teams?.[team]?.palettes?.[skin]))return false;
  const frames=data.cycles?.[screenDirection],extra=data.team_palette[team];
  if(!Array.isArray(frames)||frames.length!==duration||!Array.isArray(extra)||extra.length!==4||extra.some(w=>!Number.isInteger(w)||w<0||w>0x7fff))return false;
  try{teamDetailColor(detailManifest,team,kit);}catch{return false;}
  return frames.every(f=>Array.isArray(f.parts)&&Array.isArray(f.tiles)&&(!f.detail_variants||(f.detail_variants.length===720&&Number.isInteger(f.detail_address)&&!!tileAt(f.detail_variants[team*20+shirtNumber-1]))));
 }
 return {duration,supports,frame(tick,request){
  if(!Number.isInteger(tick)||tick<0||tick>=duration||!supports(request))return null;
  const {team,kit,skin,shirtNumber,screenDirection,palette}=request,key=JSON.stringify([tick,team,kit,skin,shirtNumber,screenDirection,palette]);if(cache.has(key))return cache.get(key);
  const f=data.cycles[screenDirection][tick],vram=new Uint8Array(65536);
  for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>65536)throw Error('Tile da ação inválido');vram.set(bytes,tile.address);}
  const cgram=decode(f.cgram);if(cgram.length!==512)throw Error('Paleta da ação inválida');
  const skinWords=preview.teams[team].palettes[skin];
  for(let i=0;i<16;i++){let word=skinWords[i];if(i>=7){const c=palette[i],r=Math.round(parseInt(c.slice(1,3),16)*31/255),g=Math.round(parseInt(c.slice(3,5),16)*31/255),b=Math.round(parseInt(c.slice(5,7),16)*31/255);word=r|(g<<5)|(b<<10);}const p=(128+16+i)*2;cgram[p]=word&255;cgram[p+1]=word>>8;}
  if(f.detail_variants){const detail=tileAt(f.detail_variants[team*20+shirtNumber-1]);if(f.detail_address<0||f.detail_address+32>65536)throw Error('Detalhe de uniforme inválido');vram.set(detail,f.detail_address);const rgb=teamDetailColor(detailManifest,team,kit),extra=data.team_palette[team].slice();if(rgb)extra[0]=rgb.reduce((w,c,i)=>w|(Math.round(c*31/255)<<(5*i)),0);for(let i=0;i<4;i++){const p=(128+5*16+12+i)*2;cgram[p]=extra[i]&255;cgram[p+1]=extra[i]>>8;}const p=(128+5*16+10)*2;cgram[p]=data.palette10&255;cgram[p+1]=data.palette10>>8;}
  const image=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96}),canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),pixels=ctx.createImageData(96,96);pixels.data.set(image.rgba);ctx.putImageData(pixels,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}

export function createNativeJumpBody(data,preview,detailManifest,makeCanvas){
 return createNativeCapturedAction(data,preview,detailManifest,makeCanvas,{schema:'issd-jump-directions-local/v1',duration:23});
}
