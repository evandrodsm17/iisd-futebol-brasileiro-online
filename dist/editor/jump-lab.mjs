import {createNativeJumpBody} from '../native-jump-body.mjs';
import {composeOam} from '../native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// One captured actor and kit. Every pose, offset, palette and duration came
// from the paired replay; this is not yet a general player action renderer.
export function createJumpCapture(data,makeCanvas){
 if(data?.schema!=='issd-jump-lab-local/v1'||data.width!==96||data.height!==96||data.ticks_per_second!==60||!Array.isArray(data.frames)||data.frames.length!==23)throw Error('Dados locais do salto incompatíveis');
 const cache=new Map();
 return {duration:data.frames.length,frame(index){
  if(!Number.isInteger(index)||index<0||index>=data.frames.length)return null;
  if(cache.has(index))return cache.get(index);
  const f=data.frames[index];if(!Array.isArray(f.parts)||!Array.isArray(f.tiles))throw Error('Quadro do salto inválido');
  const vram=new Uint8Array(65536);for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>65536)throw Error('Tile do salto inválido');vram.set(bytes,tile.address);}
  const cgram=decode(f.cgram);if(cgram.length!==512)throw Error('Paleta do salto inválida');
  const image=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96}),canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),pixels=ctx.createImageData(96,96);pixels.data.set(image.rgba);ctx.putImageData(pixels,0,0);cache.set(index,canvas);return canvas;
 }};
}

export async function startJumpLab(doc,env={}){
 const byId=id=>doc.getElementById(id),fetcher=env.fetch??fetch,schedule=env.requestFrame??requestAnimationFrame;
 const el=Object.fromEntries(['demo','play','tick','frame','status','team','kit','direction','skin','shirt'].map(k=>[k,byId('jump-'+k)]));
 if(Object.values(el).some(v=>!v))throw Error('Painel de salto incompleto');
 const response=await fetcher('../assets/issd/slide-lab-local/jump.json');if(!response.ok)throw Error('Prévia local não encontrada; gere os dados a partir da captura.');
 const make=env.makeCanvas??((w,h)=>{const canvas=doc.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;});
 const captured=createJumpCapture(await response.json(),make);
 const optional=async path=>{try{const r=await fetcher(path);return r.ok?await r.json():null;}catch{return null;}};
 const [data,preview,detail,catalog]=await Promise.all([optional('../assets/issd/slide-lab-local/jump-directions.json'),optional('../assets/issd/editor-preview-local.json'),optional('../data/issd-team-detail-colors.json'),optional('../data/issd-rom-catalog.json')]);
 const dynamic=data?.schema==='issd-jump-directions-local/v1'&&preview?.schema==='issd-editor-preview-local/v1'&&detail?.schema==='issd-team-detail-colors/v1'&&Array.isArray(catalog?.teams)?createNativeJumpBody(data,preview,detail,make):null;
 if(dynamic){el.team.replaceChildren(...catalog.teams.map(t=>{const o=doc.createElement('option');o.value=String(t.id);o.textContent=t.name;return o;}));el.team.value='2';for(const k of ['team','kit','direction','skin','shirt'])el[k].disabled=false;}
 const ctx=el.demo.getContext('2d');let playing=true,tick=0,last=null;
 function draw(){
  const current=Math.floor(tick);el.tick.max=String(captured.duration-1);el.tick.value=String(current);el.frame.textContent=`${current+1} / ${captured.duration}`;ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;
  if(!dynamic){ctx.drawImage(captured.frame(current),0,0);el.status.textContent='Captura lateral original; gere os dados dinâmicos para escolher equipe e direção.';return;}
  const team=Number(el.team.value),kit=el.kit.value,request={team,kit,skin:Number(el.skin.value),shirtNumber:Number(el.shirt.value),screenDirection:Number(el.direction.value),palette:catalog.teams[team]?.kit?.[kit]?.sprite_palette};
  if(!dynamic.supports(request)){el.status.textContent='Direção ou combinação ainda não validada para esta prévia.';return;}
  ctx.drawImage(dynamic.frame(current,request),0,0);el.status.textContent='Corpo capturado com uniforme da equipe; cabelo ainda não validado.';
 }
 for(const k of ['team','kit','direction','skin','shirt'])el[k].addEventListener('change',()=>{tick=0;last=null;draw();});
 el.play.disabled=false;el.play.addEventListener('click',()=>{playing=!playing;el.play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 el.tick.addEventListener('input',()=>{tick=Math.max(0,Math.min(captured.duration-1,Number(el.tick.value)||0));playing=false;el.play.textContent='Reproduzir';last=null;draw();});
 function animate(now){if(last!==null&&playing)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%captured.duration;last=now;draw();schedule(animate);}
 draw();schedule(animate);
}
