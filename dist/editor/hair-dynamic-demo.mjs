// Four verified frames only. This demonstration does not modify gameplay.
export async function startDynamicDemo(canvas,status){
 const [auditResponse,atlasResponse]=await Promise.all([
  fetch('../data/issd-dynamic-hair-anchor-audit.json'),
  fetch('../assets/issd/editor-preview-local.json')]);
 if(!auditResponse.ok||!atlasResponse.ok)throw Error('Dados locais da montagem não encontrados.');
 const audit=await auditResponse.json(),atlas=await atlasResponse.json();
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
 function draw(){
  const f=audit.frames[frame],originX=32,originY=48;
  ctx.clearRect(0,0,64,64);ctx.imageSmoothingEnabled=false;
  ctx.drawImage(corrected,f.sheet_frame*audit.cell_width,0,audit.cell_width,audit.cell_height,
    originX-f.origin_x,originY-f.origin_y,audit.cell_width,audit.cell_height);
  const tile=Uint8Array.from(atob(atlas.hair_tiles[0][f.selector-1]),c=>c.charCodeAt(0));
  if(tile.length!==64)throw Error('Tile de cabelo inválido.');
  const pixels=ctx.createImageData(8,8);
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){
   const index=tile[y*8+(7-x)],rgba=audit.palette_rgb[index];
   if(index){const p=(y*8+x)*4;pixels.data[p]=rgba[0];pixels.data[p+1]=rgba[1];pixels.data[p+2]=rgba[2];pixels.data[p+3]=255;}
  }
  const layer=document.createElement('canvas');layer.width=8;layer.height=8;layer.getContext('2d').putImageData(pixels,0,0);
  ctx.drawImage(layer,originX+f.hair_x,originY+f.hair_y);
 }
 function tick(now){if(now-last>=180){frame=(frame+1)%audit.frames.length;last=now;draw();}requestAnimationFrame(tick);}
 draw();status.textContent='Folha de corpo + âncoras + atlas de cabelo: 4 quadros validados.';requestAnimationFrame(tick);
}
