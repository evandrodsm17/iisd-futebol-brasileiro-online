import {renderRuntimeBody} from './native-runtime-body.mjs';

// Three observed poses per synthetic replay. Prediction and contact remain
// browser heuristics; the second direction was forced in emulator memory.
export function createKeeperDive(data,preview,makeCanvas){
 if(data?.schema!=='issd-keeper-dive-local/v2'||data.width!==96||data.height!==96||!data.cycles||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados de mergulho incompatíveis');
 for(const [direction,cycle] of Object.entries(data.cycles))if(!['1','2','5','6'].includes(direction)||cycle.frames?.length!==3||cycle.ticks?.join(',')!=='1,7,28')throw Error('Ciclo de mergulho incompatível');
 const cache=new Map();
 function supports(request){const {team,skin,screenDirection}=request;const palette=preview.teams?.[team]?.palettes?.[2+skin];return Number.isInteger(team)&&team>=0&&team<36&&[0,1].includes(skin)&&!!data.cycles[screenDirection]&&Array.isArray(palette)&&palette.length===16&&palette.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);}
 return {supports,duration:36,frame(ticks,request){
  if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=36)return null;
  const index=ticks<1?0:ticks<8?1:2,key=`${request.team}/${request.skin}/${request.screenDirection}/${index}`;if(cache.has(key))return cache.get(key);
  const palette=preview.teams[request.team].palettes[2+request.skin].map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
  const result=renderRuntimeBody({...data.cycles[request.screenDirection],width:data.width,height:data.height},index,palette,{4:palette}),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=216)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadKeeperDive(){
 const responses=await Promise.all(['./assets/issd/native-keeper-dive-local.json','./assets/issd/editor-preview-local.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Dados locais de mergulho indisponíveis');
 const [data,preview]=await Promise.all(responses.map(r=>r.json()));
 return createKeeperDive(data,preview,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
