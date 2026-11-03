import {composeOam} from '../native-oam-compositor.mjs';

const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

export async function startSlideDemo(canvas,status,button,label) {
 const response=await fetch('../assets/issd/slide-lab-local/preview.json');
 if(!response.ok)throw Error('Prévia local indisponível. Gere os dados a partir da captura local.');
 const data=await response.json();
 if(data?.schema!=='issd-slide-lab-local/v1'||data.width!==96||data.height!==96||!Array.isArray(data.frames)||data.frames.length!==6)throw Error('Dados da prévia de carrinho inválidos.');
 const ctx=canvas.getContext('2d');
 const frames=data.frames.map(frame=>{
  if(!Number.isInteger(frame.ticks)||frame.ticks<1||!Array.isArray(frame.tiles))throw Error('Quadro de carrinho inválido.');
  const vram=new Uint8Array(65536);
  for(const tile of frame.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>vram.length)throw Error('Tile inválido.');vram.set(bytes,tile.address);}
  const result=composeOam({vram,cgram:decode(frame.cgram),obsel:frame.obsel,parts:frame.parts,width:96,height:96});
  const pixels=ctx.createImageData(96,96);pixels.data.set(result.rgba);return {pixels,ticks:frame.ticks,descriptor:frame.descriptor};
 });
 const duration=frames.reduce((sum,frame)=>sum+frame.ticks,0);
 let playing=true,last=null,position=0,shown=-1;
 const draw=()=>{let tick=Math.floor(position)%duration,index=0;while(tick>=frames[index].ticks){tick-=frames[index].ticks;index++;}if(index!==shown){ctx.putImageData(frames[index].pixels,0,0);label.textContent=`Pose ${index+1} / ${frames.length}`;shown=index;}};
 button.disabled=false;button.addEventListener('click',()=>{playing=!playing;button.textContent=playing?'Pausar':'Reproduzir';last=null;});
 status.textContent='Prévia local carregada · corpo observado em uma direção.';
 function tick(now){if(last!==null&&playing)position=(position+Math.min(now-last,100)*60/1000)%duration;last=now;draw();requestAnimationFrame(tick);}
 draw();requestAnimationFrame(tick);
}
