import {renderRuntimeBody} from './native-runtime-body.mjs';

// The currently exported ROM data covers one captured appearance and a subset
// of directions; everything else stays on the safe player-specific fallback.
export function createNativePassBody(data, makeCanvas, locomotion) {
 const validPalette=p=>Array.isArray(p)&&p.length===16&&p.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);
 if(data?.schema!=='issd-pass-body-local/v2'||data.team!==2||data.kit!=='home'||data.skin!==0||data.hair!==0||!validPalette(data.palette)||!validPalette(data.extra_palette)||!data.cycles||locomotion?.schema!=='issd-runtime-body-local/v1')throw Error('Dados locais do passe incompatíveis');
 const romDirection=[6,7,0,1,2,3,4,5],heights={};
 for(const [direction,cycle] of Object.entries(data.cycles)){
  if(!['0','1','2','3','4','5','6','7'].includes(direction)||cycle.width!==96||cycle.height!==96||cycle.ticks?.join(',')!=='2,16'||cycle.frames?.length!==2)throw Error('Ciclo do passe incompatível');
  const height=locomotion.cycles?.walking?.[romDirection[Number(direction)]]?.height;
  if(!Number.isInteger(height)||height<1||height>256)throw Error('Escala de locomoção indisponível');
  heights[direction]=height;
 }
 const toColors=words=>words.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
 const palette=toColors(data.palette),banks={1:palette,5:toColors(data.extra_palette)},cache=new Map();
 return {
  supports({team,kit,appearance,position,screenDirection}){return team===data.team&&kit===data.kit&&position!=='GK'&&appearance?.skin_tone===data.skin&&appearance?.hair_style===data.hair&&!!data.cycles[screenDirection];},
  referenceHeight(screenDirection){return heights[screenDirection]??null;},
  frame(ticks,screenDirection){
   const cycle=data.cycles[screenDirection];if(!cycle||!Number.isFinite(ticks)||ticks<0||ticks>=18)return null;
   const index=ticks<2?0:1,key=`${screenDirection}/${index}`;if(cache.has(key))return cache.get(key);
   const result=renderRuntimeBody(cycle,index,palette,banks),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
   image.data.set(result.rgba);ctx.putImageData(image,0,0);cache.set(key,canvas);return canvas;
  },
  duration:18,
 };
}
export async function loadNativePassBody(){
 const [response,motionResponse]=await Promise.all([fetch('./assets/issd/native-pass-body-local.json'),fetch('./assets/issd/runtime-body-local.json')]);
 if(!response.ok||!motionResponse.ok)throw Error('Dados locais do passe ou locomoção indisponíveis');
 return createNativePassBody(await response.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},await motionResponse.json());
}
