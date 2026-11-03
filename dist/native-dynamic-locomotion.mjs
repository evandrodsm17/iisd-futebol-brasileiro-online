import { teamDetailColor } from './native-team-detail-color.mjs';

// This narrow adapter only accepts the captured England/home walking frames.
// Body pixels still come from the existing sheet; hair and detail are composed
// from indexed local ROM resources. Other poses must keep their existing path.
export function createDynamicLocomotion({audit, atlas, details, colors, image, makeCanvas}) {
 if(audit?.schema!=='issd-dynamic-hair-audit/v1'||audit.team!==2||audit.kit!=='home'||audit.motion!=='walking'||audit.direction!==4||audit.style!==1||atlas?.schema!=='issd-editor-preview-local/v1')throw Error('Dados de composição incompatíveis');
 const frames=new Map();
 for(const item of audit.frames)if(!frames.has(item.sheet_frame))frames.set(item.sheet_frame,item);
 const cache=new Map();
 function tile(ctx,indices,palette,x,y,flipX,flipY){
  if(indices.length!==64)throw Error('Tile inválido');
  const layer=makeCanvas(8,8),lc=layer.getContext('2d'),pixels=lc.createImageData(8,8);
  for(let py=0;py<8;py++)for(let px=0;px<8;px++){
   const index=indices[(flipY?7-py:py)*8+(flipX?7-px:px)];
   if(index){const rgb=palette[index];if(!rgb)throw Error('Paleta incompleta');const p=(py*8+px)*4;pixels.data.set([...rgb,255],p);}
  }
  lc.putImageData(pixels,0,0);ctx.drawImage(layer,x,y);
 }
 function compose(frame){
  if(cache.has(frame))return cache.get(frame);
  const f=frames.get(frame);if(!f)return null;
  const canvas=makeCanvas(audit.cell_width,audit.cell_height),ctx=canvas.getContext('2d',{willReadFrequently:true});
  ctx.drawImage(image,frame*audit.cell_width,0,audit.cell_width,audit.cell_height,0,0,audit.cell_width,audit.cell_height);
  const pixels=ctx.getImageData(0,0,audit.cell_width,audit.cell_height),map=new Map();
  for(let i=0;i<32;i++)map.set(Math.floor(i*255/31),(i<<3)|(i>>2));
  for(let i=0;i<pixels.data.length;i+=4)if(pixels.data[i+3])for(let c=0;c<3;c++){
   const value=map.get(pixels.data[i+c]);if(value===undefined)throw Error('Cor de corpo inválida');pixels.data[i+c]=value;
  }
  ctx.putImageData(pixels,0,0);
  if(f.detail){
   const detail=details.tiles[String(f.step)],color=teamDetailColor(colors,audit.team,audit.kit);
   if(!detail||detail.pixels.some(index=>index!==0&&index!==12)||!color||color.some((v,i)=>v!==detail.palette_rgb[12][i]))throw Error('Detalhe não validado');
   const palette=detail.palette_rgb.map(rgb=>rgb.slice());palette[12]=color;
   tile(ctx,detail.pixels,palette,f.origin_x+f.detail.x,f.origin_y+f.detail.y,f.detail.h_flip,f.detail.v_flip);
  }
  const hair=Uint8Array.from(atob(atlas.hair_tiles[0][f.selector-1]),c=>c.charCodeAt(0));
  tile(ctx,hair,audit.palette_rgb,f.origin_x+f.hair_x,f.origin_y+f.hair_y,true,false);
  cache.set(frame,canvas);return canvas;
 }
 return {frame({team,kit,motion,direction,appearance,position,frame}){
  if(team!==2||kit!=='home'||motion!=='walking'||direction!==4||appearance?.hair_style!==1||appearance?.skin_tone!==0||position==='GK')return null;
  return compose(frame);
 }};
}

export async function loadDynamicLocomotion(){
 const read=async path=>{const response=await fetch(path);if(!response.ok)throw Error(`Arquivo local indisponível: ${path}`);return response.json();};
 const [audit,atlas,details,colors]=await Promise.all([
  read('./data/issd-dynamic-hair-anchor-audit.json'),read('./assets/issd/editor-preview-local.json'),
  read('./assets/issd/hair-lab-local/dynamic-detail-local.json'),read('./data/issd-team-detail-colors.json')]);
 const image=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('Folha local indisponível'));img.src='./assets/issd/oam-teams/02/home/walking-4.png';});
 if(image.naturalWidth%audit.cell_width||image.naturalHeight!==audit.cell_height)throw Error('Dimensões da folha inválidas');
 return createDynamicLocomotion({audit,atlas,details,colors,image,makeCanvas:(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;}});
}
