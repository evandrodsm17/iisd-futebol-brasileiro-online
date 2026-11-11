import {DRIBBLE,settleDribble} from './dribble-contact.mjs';
import {pickupPlayer} from './ball-contact.mjs';
import {PASS_FRICTION} from './pass-model.mjs';
import {classifyFieldExit} from './field-events.mjs';

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

// Applies the same provisional line-crossing and restart policy as local play.
export function resolveOnlineFieldExit(previous,ball,field,lastTouchTeam,handlers){
 const event=classifyFieldExit(previous,ball,field,lastTouchTeam);
 if(!event)return null;
 if(event.type==='goal')handlers.goal(event.team);
 else handlers.restart(event.type==='throw_in'?'LATERAL':event.type==='corner'?'ESCANTEIO':'TIRO DE META',event.x,event.y,event.team);
 return event;
}
