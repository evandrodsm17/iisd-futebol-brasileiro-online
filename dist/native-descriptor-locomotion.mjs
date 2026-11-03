import {applyDescriptorRows,composeOam,decodeOamParts} from './native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// Replay-backed first integration: positions, palette, hair and detail remain
// captured; only the body graphics rows are selected from ROM descriptors.
export function createDescriptorLocomotion(data,makeCanvas){
 if(data?.schema!=='issd-descriptor-bridge-demo-local/v1'||data.frames?.length!==10)throw Error('Dados locais incompatíveis');
 const cache=new Map();
 return {frame({team,kit,motion,direction,appearance,position,frame}){
  if(team!==2||kit!=='home'||motion!=='walking'||direction!==4||appearance?.hair_style!==1||appearance?.skin_tone!==0||position==='GK')return null;
  if(!Number.isInteger(frame)||frame<0||frame>=data.frames.length)return null;
  if(cache.has(frame))return cache.get(frame);
  const f=data.frames[frame],oam=decode(f.oam),parts=decodeOamParts(oam,f.obsel,f.slots);
  const vram=applyDescriptorRows(decode(f.vram),decode(f.rows),{obsel:f.obsel,baseTile:f.base_tile,bank:f.bank});
  const image=composeOam({vram,cgram:decode(f.cgram),obsel:f.obsel,parts});
  const full=makeCanvas(256,224),ctx=full.getContext('2d'),pixels=ctx.createImageData(256,224);
  pixels.data.set(image.rgba);ctx.putImageData(pixels,0,0);
  const cell=makeCanvas(f.cell_width,f.cell_height);cell.getContext('2d').drawImage(full,f.crop_x,f.crop_y,f.cell_width,f.cell_height,0,0,f.cell_width,f.cell_height);
  cache.set(frame,cell);return cell;
 }};
}

export async function loadDescriptorLocomotion(){
 const response=await fetch('./assets/issd/hair-lab-local/descriptor-bridge-demo-local.json');
 if(!response.ok)throw Error('Dados locais dos descritores indisponíveis');
 const data=await response.json();return createDescriptorLocomotion(data,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
