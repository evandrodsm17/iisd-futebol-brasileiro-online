const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
export function idleDescriptor(cycle,ticks,durations,withBall){
 if(withBall){const observed=new Set(cycle.frames.map(f=>f.descriptor));return cycle.sequence.find(d=>observed.has(d))??null;}
 const total=durations.reduce((a,b)=>a+b,0);let time=((Math.floor(ticks)%total)+total)%total;
 for(let i=0;i<durations.length;i++){if(time<durations[i])return cycle.sequence[i];time-=durations[i];}
 return null;
}
export function renderIdleFrame(cycle,descriptor,palette){
 const frame=cycle.frames.find(item=>item.descriptor===descriptor);
 const banks=Array.isArray(palette?.[0])?palette:Array.from({length:8},()=>palette);
 if(!frame||banks.length!==8||banks.some(bank=>!Array.isArray(bank)||bank.length!==16||bank.some(c=>typeof c!=='string'||!/^#[0-9a-f]{6}$/i.test(c))))throw Error('Pose ou paleta parada inválida');
 const rgba=new Uint8ClampedArray(cycle.width*cycle.height*4),colors=banks.map(bank=>bank.map(v=>[1,3,5].map(i=>parseInt(v.slice(i,i+2),16))));
 for(const part of [...frame.parts].reverse()){
  const pixels=decode(part.pixels);if(pixels.length!==part.size*part.size)throw Error('Peça parada inválida');
  for(let y=0;y<part.size;y++)for(let x=0;x<part.size;x++){
   const index=pixels[y*part.size+x];if(!index)continue;
   const xx=part.x-cycle.left+x,yy=part.y-cycle.top+y;if(xx<0||yy<0||xx>=cycle.width||yy>=cycle.height)throw Error('Geometria parada inválida');
   rgba.set([...colors[part.palette][index],255],(yy*cycle.width+xx)*4);
  }
 }
 return {width:cycle.width,height:cycle.height,rgba};
}
export function createIdleRenderer(data,makeCanvas){
 if(data?.schema!=='issd-idle-runtime-local/v1'||data.idle_durations?.join(',')!=='24,6,24,6')throw Error('Dados de espera incompatíveis');
 const cache=new Map();
 return {frame({team,kit,direction,withBall,ticks,palette}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||!Number.isInteger(direction)||direction<0||direction>7||typeof withBall!=='boolean'||!Number.isFinite(ticks)||!Array.isArray(palette))return null;
  const cycle=data.cycles[withBall?'idle_with_ball':'idle'][direction],desc=idleDescriptor(cycle,ticks,data.idle_durations,withBall);
  if(desc===null)return null;
  const key=JSON.stringify([team,kit,direction,withBall,desc,palette]);if(cache.has(key))return cache.get(key);
  const result=renderIdleFrame(cycle,desc,palette),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
 }};
}
export async function loadIdleRenderer(){
 const response=await fetch('./assets/issd/idle-runtime-local.json');if(!response.ok)throw Error('Dados locais de espera indisponíveis');
 return createIdleRenderer(await response.json(),(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
