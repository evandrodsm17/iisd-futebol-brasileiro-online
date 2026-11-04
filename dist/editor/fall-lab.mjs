import {composeOam} from '../native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// Body and timing of one observed victim; team variants and full recovery are
// separate investigations. Pixels come from locally generated ROM resources.
export function createFallCapture(data,makeCanvas){
 if(data?.schema!=='issd-fall-lab-local/v1'||data.width!==96||data.height!==96||data.ticks_per_second!==60||!Array.isArray(data.frames)||data.frames.length!==35)throw Error('Dados locais da queda incompatíveis');
 const cache=new Map();return {duration:data.frames.length,frame(index){
  if(!Number.isInteger(index)||index<0||index>=data.frames.length)return null;if(cache.has(index))return cache.get(index);
  const f=data.frames[index];if(!Array.isArray(f.parts)||!Array.isArray(f.tiles))throw Error('Quadro da queda inválido');
  const vram=new Uint8Array(65536);for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>65536)throw Error('Tile da queda inválido');vram.set(bytes,tile.address);}
  const cgram=decode(f.cgram);if(cgram.length!==512)throw Error('Paleta da queda inválida');
  const image=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96}),canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),pixels=ctx.createImageData(96,96);pixels.data.set(image.rgba);ctx.putImageData(pixels,0,0);cache.set(index,canvas);return canvas;
 }};
}
export async function startFallLab(doc,env={}){
 const byId=id=>doc.getElementById(id),fetcher=env.fetch??fetch,schedule=env.requestFrame??requestAnimationFrame;
 const el=Object.fromEntries(['demo','play','tick','frame','status'].map(k=>[k,byId('fall-'+k)]));if(Object.values(el).some(v=>!v))throw Error('Painel de queda incompleto');
 const response=await fetcher('../assets/issd/slide-lab-local/fall.json');if(!response.ok)throw Error('Prévia local não encontrada; gere os dados a partir da captura.');
 const make=env.makeCanvas??((w,h)=>{const c=doc.createElement('canvas');c.width=w;c.height=h;return c;});
 const fall=createFallCapture(await response.json(),make),ctx=el.demo.getContext('2d');let playing=true,tick=0,last=null;
 function draw(){const current=Math.floor(tick);el.tick.max=String(fall.duration-1);el.tick.value=String(current);el.frame.textContent=`${current+1} / ${fall.duration}`;ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;ctx.drawImage(fall.frame(current),0,0);el.status.textContent='Corpo capturado após contato entre jogadores durante o carrinho.';}
 el.play.disabled=false;el.play.addEventListener('click',()=>{playing=!playing;el.play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 el.tick.addEventListener('input',()=>{tick=Math.max(0,Math.min(fall.duration-1,Number(el.tick.value)||0));playing=false;el.play.textContent='Reproduzir';last=null;draw();});
 function animate(now){if(last!==null&&playing)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%fall.duration;last=now;draw();schedule(animate);}
 draw();schedule(animate);
}
