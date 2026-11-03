// Dynamic body equivalent to the existing team sheets. It deliberately keeps
// their single-palette and observed actor-context limitations.
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
const signed=value=>value<0x8000?value:value-0x10000;
export function renderRuntimeBody(cycle,frameIndex,palette){
 const f=cycle?.frames?.[frameIndex];
 if(!f||!Array.isArray(palette)||palette.length!==16||palette.some(c=>typeof c!=='string'||!/^#[0-9a-f]{6}$/i.test(c)))throw Error('Dados de corpo ou paleta inválidos');
 const width=cycle.width,height=cycle.height,rgba=new Uint8ClampedArray(width*height*4),tiles=decode(f.tiles);
 if(tiles.length!==0x600)throw Error('Linhas de tiles inválidas');
 const colors=palette.map(value=>[1,3,5].map(i=>parseInt(value.slice(i,i+2),16)));
 for(const p of [...f.parts].reverse()){
  const size=p.large?16:8;let dx=signed(p.dx);if(f.props&64)dx=-dx;
  const left=f.origin_x+dx-(p.large?8:4),top=f.origin_y+signed(p.dy)-(p.large?8:4);
  let attr=(p.attr&0xc1)^f.props;if(p.attr&0x20)attr=attr&8?attr|2:(attr&0xfb)|8;
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
   const sx=attr&64?size-1-x:x,sy=attr&128?size-1-y:y,dx2=left+x,dy2=top+y;
   if(dx2<0||dy2<0||dx2>=width||dy2>=height)continue;
   const tile=p.tile+(sx>>3)+16*(sy>>3),address=tile*32+(sy&7)*2,bit=7-(sx&7);
   if(address+17>=tiles.length)continue;
   const index=((tiles[address]>>bit)&1)|(((tiles[address+1]>>bit)&1)<<1)|(((tiles[address+16]>>bit)&1)<<2)|(((tiles[address+17]>>bit)&1)<<3);
   if(!index)continue;const i=(dy2*width+dx2)*4;rgba.set([...colors[index],255],i);
  }
 }
 return {width,height,rgba};
}
export function createRuntimeBody(data,makeCanvas){
 if(data?.schema!=='issd-runtime-body-local/v1')throw Error('Dados de locomoção incompatíveis');
 const cache=new Map();
 return {frame({team,kit,motion,direction,frame,palette}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||!['walking','running'].includes(motion)||!Number.isInteger(direction)||direction<0||direction>7||!Array.isArray(palette))return null;
  const cycle=data.cycles?.[motion]?.[direction];if(!cycle?.frames?.[frame])return null;
  const key=JSON.stringify([team,kit,motion,direction,frame,palette]);if(cache.has(key))return cache.get(key);
  const result=renderRuntimeBody(cycle,frame,palette),canvas=makeCanvas(result.width,result.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(result.width,result.height);
  image.data.set(result.rgba);ctx.putImageData(image,0,0);
  if(cache.size>=512)cache.delete(cache.keys().next().value);
  cache.set(key,canvas);return canvas;
 }};
}
export async function loadRuntimeBody(){
 const response=await fetch('./assets/issd/runtime-body-local.json');if(!response.ok)throw Error('Dados locais de locomoção indisponíveis');
 return createRuntimeBody(await response.json(),(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;});
}
