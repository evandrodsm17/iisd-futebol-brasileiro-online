import {DRIBBLE,settleDribble} from './dribble-contact.mjs';
import {pickupPlayer} from './ball-contact.mjs';
import {PASS_FRICTION} from './pass-model.mjs';

// Uses the existing provisional browser model; not a recovered ROM routine.
export function advanceOnlineBall(ball,humanPlayers,frames,lastTouchTeam,elapsedSinceKick){
 if(ball.owner){
  ball.passRolling=false;ball.actionKind=null;
  lastTouchTeam=ball.owner.team;
  const contact=settleDribble(ball,ball.owner,frames);
  if(contact.distanceAfter>DRIBBLE.releaseDistance)ball.owner=null;
 }else{
  ball.x+=ball.vx*frames;ball.y+=ball.vy*frames;
  const speed=Math.hypot(ball.vx,ball.vy),nextSpeed=Math.max(0,speed-(ball.passRolling?PASS_FRICTION:.03125)*frames);
  if(speed){ball.vx*=nextSpeed/speed;ball.vy*=nextSpeed/speed;}
  ball.owner=pickupPlayer(humanPlayers,ball,lastTouchTeam,elapsedSinceKick);
 }
 return lastTouchTeam;
}
