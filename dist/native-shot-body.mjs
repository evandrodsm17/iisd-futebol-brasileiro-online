import {renderRuntimeBody} from './native-runtime-body.mjs';
import {actionFrame, durationInTicks} from './action-visual.mjs';

// One captured screen direction. Hair geometry and other directions are pending.
export function createNativeShotBody(data, makeCanvas, locomotion, preview) {
 if(data?.schema!=='issd-shot-body-local/v1'||data.screen_direction!==2||data.width!==96||data.height!==96||data.frames?.length!==6||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais do chute incompatíveis');
 const height=locomotion.cycles?.walking?.[0]?.height;
 if(!Number.isInteger(height)||height<1||height>256)throw Error('Escala de locomoção indisponível');
 const colors=words=>words.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
 const quantize=value=>'#'+[1,3,5].map(i=>{const n=Math.round(parseInt(value.slice(i,i+2),16)*31/255);return ((n<<3)|(n>>2)).toString(16).padStart(2,'0');}).join('');
 const cache=new Map();
 function supports({team,kit,appearance,position,screenDirection,palette}) {
  const skin=preview.teams?.[team]?.palettes?.[appearance?.skin_tone];
  return Number.isInteger(team)&&team>=0&&team<36&&['home','away'].includes(kit)&&position!=='GK'&&screenDirection===2&&[0,1].includes(appearance?.skin_tone)&&Array.isArray(skin)&&skin.length===16&&skin.every(n=>Number.isInteger(n)&&n>=0&&n<=0x7fff)&&Array.isArray(palette)&&palette.length===16&&palette.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 }
 return {supports,referenceHeight:()=>height,duration:durationInTicks('shot'),frame(ticks,request){
  if(!supports(request))return null;const index=actionFrame('shot',ticks);if(index===null)return null;
  const key=JSON.stringify([request.team,request.kit,request.appearance.skin_tone,index,request.palette]);if(cache.has(key))return cache.get(key);
  const palette=colors(preview.teams[request.team].palettes[request.appearance.skin_tone]).slice(0,7).concat(request.palette.slice(7).map(quantize));
  const result=renderRuntimeBody(data,index,palette,{1:palette}),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadNativeShotBody(){
 const responses=await Promise.all(['./assets/issd/native-shot-body-local.json','./assets/issd/runtime-body-local.json','./assets/issd/editor-preview-local.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Dados locais do chute indisponíveis');
 const [body,motion,preview]=await Promise.all(responses.map(r=>r.json()));
 return createNativeShotBody(body,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},motion,preview);
}
