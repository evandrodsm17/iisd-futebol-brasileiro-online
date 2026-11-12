import {DRIBBLE,settleDribble} from './dribble-contact.mjs';
import {pickupPlayer,collectAirborneThrow} from './ball-contact.mjs';
import {PASS_FRICTION} from './pass-model.mjs';
import {classifyFieldExit} from './field-events.mjs';

// Uses the existing provisional browser model; not a recovered ROM routine.
export function advanceOnlineBall(ball,humanPlayers,frames,lastTouchTeam,elapsedSinceKick,onAirborneReception,field){
 if(ball.owner){
  ball.passRolling=false;ball.actionKind=null;
  lastTouchTeam=ball.owner.team;
  const contact=settleDribble(ball,ball.owner,frames);
  if(contact.distanceAfter>DRIBBLE.releaseDistance)ball.owner=null;
 }else{
  const previous=field?{x:ball.x,y:ball.y,z:ball.z}:null;
  ball.x+=ball.vx*frames;ball.y+=ball.vy*frames;
  if(ball.actionKind==='throw_in'){
   ball.z+=ball.vz*frames;
   if(ball.z<0)ball.vz+=ball.gravity*frames;
   else if(ball.vz>.25){ball.z=0;ball.vz*=-.75;}
   else {ball.z=ball.vz=0;ball.actionKind=null;}
   // On the impact tick z is clamped to zero but a negative vz means that
   // the ball is already bouncing upward, not rolling on the ground.
   if(ball.z<0||ball.vz<0){
    if(previous&&classifyFieldExit(previous,ball,field,lastTouchTeam))return lastTouchTeam;
    const receiver=collectAirborneThrow(humanPlayers,ball,lastTouchTeam,elapsedSinceKick,onAirborneReception);return receiver?.team??lastTouchTeam;
   }
  }
  // Pickup is tested at the end of the step; an earlier line crossing wins.
  if(previous&&classifyFieldExit(previous,ball,field,lastTouchTeam))return lastTouchTeam;
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
