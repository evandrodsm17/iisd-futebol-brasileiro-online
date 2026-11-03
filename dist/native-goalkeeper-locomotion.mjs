import {renderRuntimeBody} from './native-runtime-body.mjs';

const DURATIONS=[4,3,3,3,4,3,3,3]; // $82:E35A
export function goalkeeperFrameIndex(ticks){
 let t=((Math.floor(ticks)%26)+26)%26;
 for(let i=0;i<DURATIONS.length;i++){if(t<DURATIONS[i])return i;t-=DURATIONS[i];}
 return 0;
}
export function createGoalkeeperLocomotion(data,preview,makeCanvas){
 if(data?.schema!=='issd-goalkeeper-locomotion-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados do goleiro inválidos');
 const cache=new Map();
 return {frame({team,direction,appearance,ticks}){
  const skin=appearance?.skin_tone??0;
  if(!Number.isInteger(team)||team<0||team>=36||!Number.isInteger(direction)||direction<0||direction>7||![0,1].includes(skin)||!Number.isFinite(ticks))return null;
  const cycle=data.cycles[direction],index=goalkeeperFrameIndex(ticks);
  if(!cycle?.frames?.[index])return null;
  const key=`${team}/${direction}/${skin}/${index}`;if(cache.has(key))return cache.get(key);
  const words=preview.teams[team].palettes[2+skin];
  if(!Array.isArray(words)||words.length!==16)throw Error('Paleta do goleiro inválida');
  const palette=words.map(word=>'#'+[0,5,10].map(shift=>Math.round(((word>>shift)&31)*255/31).toString(16).padStart(2,'0')).join(''));
  const result=renderRuntimeBody(cycle,index,palette),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadGoalkeeperLocomotion(){
 const [response,previewResponse]=await Promise.all([fetch('./assets/issd/goalkeeper-locomotion-local.json'),fetch('./assets/issd/editor-preview-local.json')]);
 if(!response.ok||!previewResponse.ok)throw Error('Dados locais do goleiro indisponíveis');
 return createGoalkeeperLocomotion(await response.json(),await previewResponse.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
