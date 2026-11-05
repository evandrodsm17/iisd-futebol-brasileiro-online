// Temporary browser pass assist and ground friction; these values are not yet
// calibrated to the ISSD ball's native coordinate and velocity units.
export const PASS_FRICTION=0.04;
const MAX_TARGET_DISTANCE=150,MIN_TARGET_DISTANCE=12,MIN_ALIGNMENT=0.6;

export function choosePassTarget(players,actor,ball,direction){
 if(!Array.isArray(players)||!actor||![ball?.x,ball?.y,direction?.x,direction?.y].every(Number.isFinite))return null;
 const directionLength=Math.hypot(direction.x,direction.y);if(!directionLength)return null;
 let best=null,bestScore=-Infinity;
 for(const player of players){
  if(player===actor||player.team!==actor.team||![player.x,player.y].every(Number.isFinite))continue;
  const dx=player.x-ball.x,dy=player.y-ball.y,distance=Math.hypot(dx,dy);
  if(distance<MIN_TARGET_DISTANCE||distance>MAX_TARGET_DISTANCE)continue;
  const alignment=(dx*direction.x+dy*direction.y)/(distance*directionLength);
  if(alignment<MIN_ALIGNMENT)continue;
  const score=alignment*2-distance/MAX_TARGET_DISTANCE;
  if(score>bestScore){best=player;bestScore=score;}
 }
 return best;
}

export function planGroundPass(ball,direction,target=null){
 if(![ball?.x,ball?.y,direction?.x,direction?.y].every(Number.isFinite))throw new RangeError('Passe inválido');
 let dx=direction.x,dy=direction.y,speed=2.5;
 if(target&&[target.x,target.y].every(Number.isFinite)){
  dx=target.x-ball.x;dy=target.y-ball.y;
  const distance=Math.hypot(dx,dy);
  if(distance>0)speed=Math.min(3.6,Math.sqrt(2*PASS_FRICTION*(distance+4)));
 }
 const length=Math.hypot(dx,dy);
 if(!length)throw new RangeError('Direção de passe inválida');
 return {direction:{x:dx/length,y:dy/length},speed};
}
