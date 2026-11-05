import {renderRuntimeBody} from './native-runtime-body.mjs';
import {actionFrame, durationInTicks} from './action-visual.mjs';
import {teamDetailColor} from './native-team-detail-color.mjs';

// Each direction is independently captured. Hair geometry remains pending.
export function createNativeShotBody(data, makeCanvas, locomotion, preview, detailManifest) {
 if(data?.schema!=='issd-shot-body-local/v2'||!data.cycles||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1'||detailManifest?.schema!=='issd-team-detail-colors/v1')throw Error('Dados locais do chute incompatíveis');
 const romDirection=[6,7,0,1,2,3,4,5],heights={};
 for(const [direction,cycle] of Object.entries(data.cycles)){
  const h=locomotion.cycles?.walking?.[romDirection[Number(direction)]]?.height;
  if(!['0','1','2','3','4','5','6','7'].includes(direction)||cycle.width!==96||cycle.height!==96||cycle.frames?.length!==6||!Number.isInteger(h)||h<1||h>256)throw Error('Ciclo de chute incompatível');
  heights[direction]=h;
 }
 const colors=words=>words.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
 const quantize=value=>'#'+[1,3,5].map(i=>{const n=Math.round(parseInt(value.slice(i,i+2),16)*31/255);return ((n<<3)|(n>>2)).toString(16).padStart(2,'0');}).join('');
 const cache=new Map();
 function supports({team,kit,appearance,position,screenDirection,palette,shirtNumber}) {
  const skin=preview.teams?.[team]?.palettes?.[appearance?.skin_tone];
  return Number.isInteger(team)&&team>=0&&team<36&&['home','away'].includes(kit)&&position!=='GK'&&!!data.cycles[screenDirection]&&Number.isInteger(shirtNumber)&&shirtNumber>=1&&shirtNumber<=20&&[0,1].includes(appearance?.skin_tone)&&Array.isArray(skin)&&skin.length===16&&skin.every(n=>Number.isInteger(n)&&n>=0&&n<=0x7fff)&&Array.isArray(palette)&&palette.length===16&&palette.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 }
 return {supports,referenceHeight:direction=>heights[direction]??null,duration:durationInTicks('shot'),frame(ticks,request){
  if(!supports(request))return null;const index=actionFrame('shot',ticks);if(index===null)return null;
  const key=JSON.stringify([request.team,request.kit,request.appearance.skin_tone,request.screenDirection,request.shirtNumber,index,request.palette]);if(cache.has(key))return cache.get(key);
  const palette=colors(preview.teams[request.team].palettes[request.appearance.skin_tone]).slice(0,7).concat(request.palette.slice(7).map(quantize));
  const original=data.cycles[request.screenDirection].frames[index],bytes=Uint8Array.from(atob(original.tiles),c=>c.charCodeAt(0)),variant=original.detail_variants?.[request.shirtNumber-1];
  if(bytes.length!==0x600||!variant)throw Error('Detalhe de chute indisponível');
  const detail=Uint8Array.from(atob(variant),c=>c.charCodeAt(0));if(detail.length!==32)throw Error('Detalhe de chute inválido');bytes.set(detail,23*32);
  const cycle={...data.cycles[request.screenDirection],frames:data.cycles[request.screenDirection].frames.map((f,i)=>i===index?{...f,tiles:btoa(String.fromCharCode(...bytes))}:f)};
  const extra=colors(data.extra_palette),defaults=data.team_palette?.[request.team];
  if(!Array.isArray(defaults)||defaults.length!==4)throw Error('Paleta de detalhe indisponível');
  for(let i=0;i<4;i++)extra[12+i]=colors([defaults[i]])[0];extra[10]=colors([data.palette10])[0];
  const detailColor=teamDetailColor(detailManifest,request.team,request.kit);if(detailColor)extra[12]='#'+detailColor.map(c=>c.toString(16).padStart(2,'0')).join('');
  const result=renderRuntimeBody(cycle,index,palette,{1:palette,5:extra}),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadNativeShotBody(){
 const responses=await Promise.all(['./assets/issd/native-shot-body-local.json','./assets/issd/runtime-body-local.json','./assets/issd/editor-preview-local.json','./data/issd-team-detail-colors.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Dados locais do chute indisponÃ­veis');
 const [body,motion,preview,detail]=await Promise.all(responses.map(r=>r.json()));
 return createNativeShotBody(body,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},motion,preview,detail);
}
