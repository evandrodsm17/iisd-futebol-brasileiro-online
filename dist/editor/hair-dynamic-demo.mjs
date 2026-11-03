import {teamDetailColor} from '../native-team-detail-color.mjs';
// Captured, verified frames only. This demonstration does not modify gameplay.
export async function startDynamicDemo(canvas,status){
 const [auditResponse,atlasResponse,detailResponse,colorResponse]=await Promise.all([
  fetch('../data/issd-dynamic-hair-anchor-audit.json'),
  fetch('../assets/issd/editor-preview-local.json'),
  fetch('../assets/issd/hair-lab-local/dynamic-detail-local.json'),
  fetch('../data/issd-team-detail-colors.json')]);
 if(!auditResponse.ok||!atlasResponse.ok||!detailResponse.ok||!colorResponse.ok)throw Error('Dados locais da montagem não encontrados.');
 const audit=await auditResponse.json(),atlas=await atlasResponse.json(),detailData=await detailResponse.json(),colors=await colorResponse.json();
 if(audit.schema!=='issd-dynamic-hair-audit/v1'||audit.style!==1||audit.direction!==4||!audit.frames.length||atlas.schema!=='issd-editor-preview-local/v1')throw Error('Dados da montagem inválidos.');
 const image=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('Folha de locomoção local indisponível.'));img.src='../assets/issd/oam-teams/02/home/walking-4.png';});
 const corrected=document.createElement('canvas');corrected.width=image.naturalWidth;corrected.height=image.naturalHeight;
 const source=corrected.getContext('2d',{willReadFrequently:true});source.drawImage(image,0,0);
 const data=source.getImageData(0,0,corrected.width,corrected.height),map=new Map();
 for(let i=0;i<32;i++)map.set(Math.floor(i*255/31),(i<<3)|(i>>2));
 for(let i=0;i<data.data.length;i+=4)if(data.data[i+3])for(let c=0;c<3;c++){
  const value=map.get(data.data[i+c]);if(value===undefined)throw Error('Cor da folha não pertence à paleta original.');data.data[i+c]=value;
 }
 source.putImageData(data,0,0);
 const ctx=canvas.getContext('2d');let frame=0,last=0;
 function drawTile(indices,palette,x,y,flipX,flipY){
  if(indices.length!==64)throw Error('Tile inválido.');
  const pixels=ctx.createImageData(8,8);
  for(let py=0;py<8;py++)for(let px=0;px<8;px++){
   const index=indices[(flipY?7-py:py)*8+(flipX?7-px:px)],rgb=palette[index];
   if(index){const p=(py*8+px)*4;pixels.data[p]=rgb[0];pixels.data[p+1]=rgb[1];pixels.data[p+2]=rgb[2];pixels.data[p+3]=255;}
  }
  const layer=document.createElement('canvas');layer.width=8;layer.height=8;layer.getContext('2d').putImageData(pixels,0,0);ctx.drawImage(layer,x,y);
 }
 function draw(){
  const f=audit.frames[frame],originX=32,originY=48;
  ctx.clearRect(0,0,64,64);ctx.imageSmoothingEnabled=false;
  ctx.drawImage(corrected,f.sheet_frame*audit.cell_width,0,audit.cell_width,audit.cell_height,
    originX-f.origin_x,originY-f.origin_y,audit.cell_width,audit.cell_height);
  if(f.detail){
   const detail=detailData.tiles[String(f.step)];if(!detail)throw Error('Detalhe de uniforme ausente.');
   if(detail.pixels.some(index=>index!==0&&index!==12))throw Error('Detalhe usa cores ainda não validadas.');
   const resolved=teamDetailColor(colors,audit.team,audit.kit),captured=detail.palette_rgb[12];
   if(!resolved||resolved.some((value,index)=>value!==captured[index]))throw Error('Cor da equipe não coincide com a captura validada.');
   const palette=detail.palette_rgb.map(rgb=>rgb.slice());palette[12]=resolved;
   drawTile(detail.pixels,palette,originX+f.detail.x,originY+f.detail.y,f.detail.h_flip,f.detail.v_flip);
  }
  const tile=Uint8Array.from(atob(atlas.hair_tiles[0][f.selector-1]),c=>c.charCodeAt(0));
  drawTile(tile,audit.palette_rgb,originX+f.hair_x,originY+f.hair_y,true,false);
 }
 function tick(now){if(now-last>=180){frame=(frame+1)%audit.frames.length;last=now;draw();}requestAnimationFrame(tick);}
 draw();status.textContent=`Folha de corpo + detalhe de uniforme + cabelo: ${audit.frames.length} amostras validadas.`;requestAnimationFrame(tick);
}
