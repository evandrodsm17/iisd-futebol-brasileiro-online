// Temporary browser-space body contact. The ROM's player/player collision
// states and native-to-field conversion are still under investigation.
const X_RADIUS=11;
const Y_RADIUS=7;
const PASSES=4;

export function resolvePlayerContacts(players,field){
 if(!Array.isArray(players)||!field||![field.x,field.y,field.w,field.h].every(Number.isFinite)||field.w<=30||field.h<=30)throw new RangeError('Campo ou jogadores inválidos');
 const left=field.x+15,right=field.x+field.w-15,top=field.y+15,bottom=field.y+field.h-15;
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 for(const p of players)if(![p.x,p.y,p.vx??0,p.vy??0].every(Number.isFinite))throw new RangeError('Posição ou velocidade de jogador inválida');
 for(let pass=0;pass<PASSES;pass++)for(let i=0;i<players.length;i++)for(let j=i+1;j<players.length;j++){
  const a=players[i],b=players[j];let dx=(b.x-a.x)/X_RADIUS,dy=(b.y-a.y)/Y_RADIUS;
  let distance=Math.hypot(dx,dy);if(distance>=1)continue;
  // Exact overlap has no normal. Stable pair order gives deterministic output.
  if(distance<1e-9){dx=1;dy=0;distance=0;}
  const nx=distance?dx/distance:1,ny=distance?dy/distance:0;
  const shiftX=(1-distance)*nx*X_RADIUS,shiftY=(1-distance)*ny*Y_RADIUS;
  const ax=clamp(a.x-shiftX/2,left,right),ay=clamp(a.y-shiftY/2,top,bottom);
  const bx=clamp(b.x+shiftX/2,left,right),by=clamp(b.y+shiftY/2,top,bottom);
  // Transfer any displacement blocked by the touchline to the other actor.
  const remainingX=shiftX-((a.x-ax)+(bx-b.x)),remainingY=shiftY-((a.y-ay)+(by-b.y));
  a.x=clamp(ax-remainingX,left,right);b.x=clamp(bx+(remainingX-(ax-a.x)),left,right);
  a.y=clamp(ay-remainingY,top,bottom);b.y=clamp(by+(remainingY-(ay-a.y)),top,bottom);
  // Remove only the approaching normal velocity; preserve tangential movement.
  const normalX=nx/X_RADIUS,normalY=ny/Y_RADIUS,norm=Math.hypot(normalX,normalY),ux=normalX/norm,uy=normalY/norm;
  const avx=a.vx??0,avy=a.vy??0,bvx=b.vx??0,bvy=b.vy??0;
  const closing=(avx-bvx)*ux+(avy-bvy)*uy;
  if(closing>0){const impulse=closing/2;a.vx=avx-impulse*ux;a.vy=avy-impulse*uy;b.vx=bvx+impulse*ux;b.vy=bvy+impulse*uy;}
 }
}
