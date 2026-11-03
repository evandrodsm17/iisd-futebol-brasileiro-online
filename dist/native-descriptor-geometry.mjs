// Observed relative geometry and attribute transformation for one captured
// actor/direction. Absolute OAM slots determine ordering, not game position.
export function buildDescriptorParts(frame){
 const state=frame?.actor_geometry,sizes=[[8,16],[8,32],[8,64],[16,32],[16,64],[32,64],[16,32],[16,32]];
 if(!Array.isArray(state?.parts)||!state.parts.length||!Array.isArray(frame.slots)||!frame.hair_geometry||!Number.isInteger(frame.origin_x)||!Number.isInteger(frame.origin_y)||!Number.isInteger(frame.obsel))throw Error('Geometria de descritor ausente');
 const slots=frame.slots.filter(slot=>slot!==frame.hair_slot);
 if(slots.length!==state.parts.length)throw Error('Quantidade de peças incompatível');
 const inherited=state.object_inherited&0x80?state.object_inherited:state.global_prop;
 const props=state.object_prop|(inherited&0x30)|(state.object_flags&0xf0),signed=n=>n<0x8000?n:n-0x10000;
 const body=state.parts.map((p,i)=>{
  let dx=signed(p.dx),attr=(p.attr&0xc1)^props;if(props&0x40)dx=-dx;
  if(p.attr&0x20)attr=attr&8?attr|2:(attr&0xfb)|8;
  return {slot:slots[i],x:frame.origin_x+dx-(p.large?8:4),y:frame.origin_y+signed(p.dy)-(p.large?8:4),
   tile:(state.tile_base+p.tile)&255,size:sizes[frame.obsel>>5][p.large?1:0],attr};
 });
 const h=frame.hair_geometry;
 return [...body,{slot:h.slot,x:frame.origin_x+h.x,y:frame.origin_y+h.y,tile:h.tile,size:h.size,attr:h.attr}];
}
