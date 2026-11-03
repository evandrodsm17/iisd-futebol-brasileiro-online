import {applyDescriptorRows,applyHairTile,composeOam,decodeOamParts} from '../native-oam-compositor.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
export async function startOamDemo(canvas,status){
 const response=await fetch('../assets/issd/hair-lab-local/oam-compositor-local.json');
 if(!response.ok)throw Error('Captura local indisponível');
 const data=await response.json();if(data.schema!=='issd-oam-demo-local/v1')throw Error('Formato de captura inválido');
 const oam=decode(data.oam),parts=decodeOamParts(oam,data.obsel,data.slots);
 const result=composeOam({vram:decode(data.vram),cgram:decode(data.cgram),obsel:data.obsel,parts});
 let left=256,top=224,right=-1,bottom=-1;
 for(let y=0;y<224;y++)for(let x=0;x<256;x++)if(result.rgba[(y*256+x)*4+3]){
  left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
 }
 if(right<left)throw Error('A captura não contém pixels visíveis');
 const layer=document.createElement('canvas');layer.width=256;layer.height=224;
 layer.getContext('2d').putImageData(new ImageData(result.rgba,256,224),0,0);
 const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);
 const width=right-left+1,height=bottom-top+1;
 ctx.drawImage(layer,left,top,width,height,Math.floor((canvas.width-width)/2),Math.floor((canvas.height-height)/2),width,height);
 status.textContent=`${parts.length} peças OAM da captura, compostas diretamente de tiles e paletas.`;
}

export async function startDescriptorDemo(canvas,status){
 const [response,hairResponse]=await Promise.all([fetch('../assets/issd/hair-lab-local/descriptor-bridge-demo-local.json'),fetch('../assets/issd/hair-lab-local/hair-descriptor-tiles-local.json')]);
 if(!response.ok||!hairResponse.ok)throw Error('Dados locais dos descritores indisponíveis');
 const [data,hair]=await Promise.all([response.json(),hairResponse.json()]);if(data.schema!=='issd-descriptor-bridge-demo-local/v1'||data.frames.length!==10||hair.schema!=='issd-hair-descriptor-tiles-local/v1')throw Error('Dados de descritores inválidos');
 const frames=data.frames.map(f=>{
  const body=applyDescriptorRows(decode(f.vram),decode(f.rows),{obsel:f.obsel,baseTile:f.base_tile,bank:f.bank,detailValidated:f.detail_validated===true});
  const parts=decodeOamParts(decode(f.oam),f.obsel,f.slots);
  const atlas=hair.styles['1'],selector=atlas.selectors[String(f.descriptor)];
  const vram=applyHairTile(body,decode(atlas.tiles[String(selector)]),{obsel:f.obsel,part:parts.find(part=>part.slot===f.hair_slot)});
  const composed=composeOam({vram,cgram:decode(f.cgram),obsel:f.obsel,parts});
  let left=256,top=224,right=-1,bottom=-1;
  for(let y=0;y<224;y++)for(let x=0;x<256;x++)if(composed.rgba[(y*256+x)*4+3]){
   left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
  }
  if(right<left)throw Error('Quadro sem pixels');
  const layer=document.createElement('canvas');layer.width=256;layer.height=224;
  layer.getContext('2d').putImageData(new ImageData(composed.rgba,256,224),0,0);
  return {layer,left,top,width:right-left+1,height:bottom-top+1};
 });
 const ctx=canvas.getContext('2d');let frame=0,last=0;
 function tick(now){if(now-last>=120){const f=frames[frame];ctx.clearRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;
  ctx.drawImage(f.layer,f.left,f.top,f.width,f.height,Math.floor((canvas.width-f.width)/2),Math.floor((canvas.height-f.height)/2),f.width,f.height);
  frame=(frame+1)%frames.length;last=now;}requestAnimationFrame(tick);}
 status.textContent='Dez quadros: linhas do descritor + OAM e paletas capturadas.';requestAnimationFrame(tick);
}
