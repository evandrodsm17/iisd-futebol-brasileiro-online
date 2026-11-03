import {composeOam,decodeOamParts} from '../native-oam-compositor.mjs';
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
