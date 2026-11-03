// Observed relative geometry and attribute transformation for one captured
// actor/direction. Absolute OAM slots determine ordering, not game position.
export function buildDescriptorParts(frame){
 if(!Array.isArray(frame?.geometry)||!frame.geometry.length||!frame.hair_geometry||!Number.isInteger(frame.attr_xor)||!Number.isInteger(frame.origin_x)||!Number.isInteger(frame.origin_y)||!Number.isInteger(frame.base_tile))throw Error('Geometria de descritor ausente');
 const body=frame.geometry.map(p=>({slot:p.slot,x:frame.origin_x+p.x,y:frame.origin_y+p.y,
  tile:(frame.base_tile+p.tile)&255,size:p.size,attr:p.attr^frame.attr_xor}));
 const h=frame.hair_geometry;
 return [...body,{slot:h.slot,x:frame.origin_x+h.x,y:frame.origin_y+h.y,tile:h.tile,size:h.size,attr:h.attr}];
}
