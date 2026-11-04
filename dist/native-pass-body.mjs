import {renderRuntimeBody} from './native-runtime-body.mjs';

// Body geometry is captured from one actor. Other team/kit colors use the same
// catalog and skin palettes as the idle renderer; hairstyles remain gated.
export function createNativePassBody(data, makeCanvas, locomotion, preview) {
 const validWords=p=>Array.isArray(p)&&p.length===16&&p.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);
 const validColors=p=>Array.isArray(p)&&p.length===16&&p.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 if(data?.schema!=='issd-pass-body-local/v2'||data.team!==2||data.kit!=='home'||data.skin!==0||data.hair!==0||!validWords(data.palette)||!validWords(data.extra_palette)||!data.cycles||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais do passe incompatíveis');
 const romDirection=[6,7,0,1,2,3,4,5],heights={};
 for(const [direction,cycle] of Object.entries(data.cycles)){
  if(!['0','1','2','3','4','5','6','7'].includes(direction)||cycle.width!==96||cycle.height!==96||cycle.ticks?.join(',')!=='2,16'||cycle.frames?.length!==2)throw Error('Ciclo do passe incompatível');
  const height=locomotion.cycles?.walking?.[romDirection[Number(direction)]]?.height;
  if(!Number.isInteger(height)||height<1||height>256)throw Error('Escala de locomoção indisponível');
  heights[direction]=height;
 }
 const toColors=words=>words.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
 const toSnesColor=value=>'#'+[1,3,5].map(i=>{const n=Math.round(parseInt(value.slice(i,i+2),16)*31/255);return ((n<<3)|(n>>2)).toString(16).padStart(2,'0');}).join('');
 const extraPalette=toColors(data.extra_palette),cache=new Map();
 function supports({team,kit,appearance,position,screenDirection,palette}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||position==='GK'||![0,1].includes(appearance?.skin_tone)||appearance?.hair_style!==0||!data.cycles[screenDirection]||!validColors(palette)||!validWords(preview.teams?.[team]?.palettes?.[appearance.skin_tone]))return false;
  // The nontransparent bank-5 detail in this direction was captured only for
  // England/home; its shape and other team selectors are not yet validated.
  return screenDirection!==0||(team===2&&kit==='home'&&appearance.skin_tone===0);
 }
 return {
  supports,
  referenceHeight(screenDirection){return heights[screenDirection]??null;},
  frame(ticks,request){
   if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=18)return null;
   const {team,kit,appearance,screenDirection,palette}=request,cycle=data.cycles[screenDirection],index=ticks<2?0:1;
   const key=JSON.stringify([team,kit,appearance.skin_tone,screenDirection,index,palette]);if(cache.has(key))return cache.get(key);
   const skin=toColors(preview.teams[team].palettes[appearance.skin_tone]),colors=skin.slice(0,7).concat(palette.slice(7).map(toSnesColor)),banks={1:colors,5:extraPalette};
   const result=renderRuntimeBody(cycle,index,colors,banks),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
   image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  },
  duration:18,
 };
}
export async function loadNativePassBody(){
 const [response,motionResponse,previewResponse]=await Promise.all([fetch('./assets/issd/native-pass-body-local.json'),fetch('./assets/issd/runtime-body-local.json'),fetch('./assets/issd/editor-preview-local.json')]);
 if(!response.ok||!motionResponse.ok||!previewResponse.ok)throw Error('Dados locais do passe ou locomoção indisponíveis');
 return createNativePassBody(await response.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},await motionResponse.json(),await previewResponse.json());
}
