// SNES 4bpp OBJ compositor. Inputs are local extracted graphics and captured
// composition data, never the ROM. This models sprite-on-sprite OAM order;
// background priority, PPU color math and scanline sprite limits are separate.
const SIZES=[[8,16],[8,32],[8,64],[16,32],[16,64],[32,64],[16,32],[16,32]];
function bytes(value,length,name){if(!(value instanceof Uint8Array)||value.length!==length)throw new Error(`${name}: tamanho inválido`);}

export function decodeOamParts(oam,obsel,slots){
 bytes(oam,544,'OAM');
 if(!Number.isInteger(obsel)||obsel<0||obsel>255||!Array.isArray(slots)||new Set(slots).size!==slots.length||slots.some(s=>!Number.isInteger(s)||s<0||s>127))throw new Error('Seleção OAM inválida');
 return slots.map(slot=>{
  const at=slot*4,high=(oam[512+(slot>>2)]>>((slot&3)*2))&3;
  return {slot,x:oam[at]-(high&1?512:0),y:oam[at+1],tile:oam[at+2],attr:oam[at+3],size:SIZES[obsel>>5][high>>1]};
 });
}

// Apply the two descriptor graphics rows to an existing PPU snapshot. Tile 23
// stays untouched until the actor-specific uniform-detail selector is known.
export function applyDescriptorRows(vram,rows,{obsel,baseTile,bank}){
 bytes(vram,65536,'VRAM');bytes(rows,0x600,'Linhas do descritor');
 if(!Number.isInteger(obsel)||obsel<0||obsel>255||!Number.isInteger(baseTile)||baseTile<0||baseTile>255||![0,1].includes(bank))throw new Error('Destino de tiles inválido');
 const copy=vram.slice(),base=((obsel&7)<<9)+(bank?(((obsel&0x18)+8)<<5):0);
 for(const tile of [...Array(8).keys(),...Array.from({length:7},(_,i)=>i+16)]){
  const address=((base+((baseTile+tile)&255))&2047)*32;
  copy.set(rows.subarray(tile*32,tile*32+32),address);
 }
 return copy;
}

export function composeOam({vram,cgram,obsel,parts,width=256,height=224}){
 bytes(vram,65536,'VRAM');bytes(cgram,512,'CGRAM');
 if(!Number.isInteger(obsel)||obsel<0||obsel>255||!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>512||height>512||!Array.isArray(parts))throw new Error('Composição inválida');
 const slots=new Set();
 for(const p of parts){
  if(!Number.isInteger(p.slot)||p.slot<0||p.slot>127||slots.has(p.slot)||!Number.isInteger(p.x)||!Number.isInteger(p.y)||!Number.isInteger(p.tile)||p.tile<0||p.tile>255||!Number.isInteger(p.attr)||p.attr<0||p.attr>255||![8,16,32,64].includes(p.size))throw new Error('Peça OAM inválida');
  slots.add(p.slot);
 }
 const rgba=new Uint8ClampedArray(width*height*4);
 for(const p of [...parts].sort((a,b)=>b.slot-a.slot)){
  const base=((obsel&7)<<9)+((p.attr&1)?(((obsel&0x18)+8)<<5):0),palette=(p.attr>>1)&7;
  for(let y=0;y<p.size;y++)for(let x=0;x<p.size;x++){
   const dx=p.x+x,dy=p.y+y;if(dx<0||dy<0||dx>=width||dy>=height)continue;
   const sx=p.attr&64?p.size-1-x:x,sy=p.attr&128?p.size-1-y:y;
   const tile=((p.tile&0xf0)|((p.tile+(sx>>3))&15))+16*(sy>>3);
   const address=((base+tile)&0x7ff)*32+(sy&7)*2,bit=7-(sx&7);
   const index=((vram[address]>>bit)&1)|(((vram[address+1]>>bit)&1)<<1)|(((vram[address+16]>>bit)&1)<<2)|(((vram[address+17]>>bit)&1)<<3);
   if(!index)continue;
   const ci=(128+palette*16+index)*2,word=cgram[ci]|(cgram[ci+1]<<8),target=(dy*width+dx)*4;
   for(let c=0;c<3;c++){const v=(word>>(c*5))&31;rgba[target+c]=(v<<3)|(v>>2);}rgba[target+3]=255;
  }
 }
 return {width,height,rgba};
}
