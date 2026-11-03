import {applyDescriptorRows,applyHairTile,composeOam,decodeOamParts} from './native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));

// OAM position and palette remain captured; body, detail and hair come from ROM.
export function createDescriptorLocomotion(data,hair,makeCanvas){
 if(data?.schema!=='issd-descriptor-bridge-demo-local/v1'||data.frames?.length!==10)throw Error('Dados locais incompatíveis');
 if(hair?.schema!=='issd-hair-descriptor-tiles-local/v1')throw Error('Atlas de cabelo incompatível');
 const cache=new Map();
 return {frame({team,kit,motion,direction,appearance,position,frame}){
  if(team!==2||kit!=='home'||motion!=='walking'||direction!==4||![1,2,13].includes(appearance?.hair_style)||appearance?.skin_tone!==0||position==='GK')return null;
  if(!Number.isInteger(frame)||frame<0||frame>=data.frames.length)return null;
  const key=`${appearance.hair_style}/${frame}`;if(cache.has(key))return cache.get(key);
  const f=data.frames[frame],oam=decode(f.oam),parts=decodeOamParts(oam,f.obsel,f.slots);
  const atlas=hair.styles[String(appearance.hair_style)],selector=atlas?.selectors[String(f.descriptor)];
  if(!selector||!atlas.tiles[String(selector)])throw Error('Tile de cabelo não validado');
  const body=applyDescriptorRows(decode(f.vram),decode(f.rows),{obsel:f.obsel,baseTile:f.base_tile,bank:f.bank,detailValidated:f.detail_validated===true});
  const vram=applyHairTile(body,decode(atlas.tiles[String(selector)]),{obsel:f.obsel,part:parts.find(part=>part.slot===f.hair_slot)});
  const image=composeOam({vram,cgram:decode(f.cgram),obsel:f.obsel,parts});
  const full=makeCanvas(256,224),ctx=full.getContext('2d'),pixels=ctx.createImageData(256,224);
  pixels.data.set(image.rgba);ctx.putImageData(pixels,0,0);
  const cell=makeCanvas(f.cell_width,f.cell_height);cell.getContext('2d').drawImage(full,f.crop_x,f.crop_y,f.cell_width,f.cell_height,0,0,f.cell_width,f.cell_height);
  cache.set(key,cell);return cell;
 }};
}

export async function loadDescriptorLocomotion(){
 const [response,hairResponse]=await Promise.all([fetch('./assets/issd/hair-lab-local/descriptor-bridge-demo-local.json'),fetch('./assets/issd/hair-lab-local/hair-descriptor-tiles-local.json')]);
 if(!response.ok||!hairResponse.ok)throw Error('Dados locais dos descritores indisponíveis');
 const [data,hair]=await Promise.all([response.json(),hairResponse.json()]);return createDescriptorLocomotion(data,hair,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
}
