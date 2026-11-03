// Local preview resources are extracted from the user's ROM; no ROM is served.
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
export function previewPixels(data,team,direction,position,skin,hair){
 if(data?.schema!=='issd-editor-preview-local/v1'||!Number.isInteger(team)||team<0||team>=data.teams.length||
    !Number.isInteger(direction)||direction<0||direction>7||![0,1].includes(skin)||!Number.isInteger(hair)||hair<0||hair>13)throw Error('Dados da prévia inválidos');
 const goalie=position==='GK',item=data.teams[team],pixels=decode(goalie?data.goalkeeper[direction]:item.body[direction]);
 if(pixels.length!==48*56)throw Error('Quadro de prévia inválido');
 if(!goalie&&hair){
  const head=data.heads[String(direction)],tile=decode(data.hair_tiles[hair-1][head.selector-1]);
  if(tile.length!==64)throw Error('Cabelo de prévia inválido');
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){
   const sx=head.attr&64?7-x:x,sy=head.attr&128?7-y:y,v=tile[sy*8+sx],xx=head.x+x,yy=head.y+y;
   if(v&&xx>=0&&xx<48&&yy>=0&&yy<56)pixels[yy*48+xx]=v;
  }
 }
 if(data.flips[goalie?'1':'0'][direction])for(let y=0;y<56;y++)for(let x=0;x<24;x++){
  const a=y*48+x,b=y*48+47-x;[pixels[a],pixels[b]]=[pixels[b],pixels[a]];
 }
 return {pixels,palette:item.palettes[(goalie?2:0)+skin]};
}
export function drawPreview(canvas,frame){
 const ctx=canvas.getContext('2d'),image=ctx.createImageData(48,56);
 for(let i=0;i<frame.pixels.length;i++){
  const index=frame.pixels[i],color=frame.palette[index]??0;
  for(let channel=0;channel<3;channel++)image.data[i*4+channel]=Math.round(((color>>(channel*5))&31)*255/31);
  image.data[i*4+3]=index?255:0;
 }
 canvas.width=48;canvas.height=56;ctx.putImageData(image,0,0);
}
