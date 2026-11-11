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
  if(ball.actionKind==='throw_in'){
   ball.z+=ball.vz*frames;
   if(ball.z<0)ball.vz+=ball.gravity*frames;
   else if(ball.vz>.25){ball.z=0;ball.vz*=-.75;}
   else {ball.z=ball.vz=0;ball.actionKind=null;}
   if(ball.z<0)return lastTouchTeam;
  }
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
