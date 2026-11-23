import {teamDefendsLeft} from './match-sides.mjs';
import {BROWSER_THROW_PASS_FLIGHT} from './throw-in.mjs';
// Provisional browser goalkeeper positioning and shot contact. Values are in
// world units, not yet calibrated to ROM collision boxes or native AI.
export function goalkeeperHome(keeper,ball,field){
 const left=teamDefendsLeft(keeper.team,field),center=field.y+field.h/2,half=field.goalH/2;
 return {x:left?field.x+32:field.x+field.w-32,y:Math.max(center-half+10,Math.min(center+half-10,ball.y))};
}

export function goalkeeperShotContact(previous,ball,players,field,lastTouchTeam){
 if(ball.actionKind!=='shot'||ball.owner||![ball.x,ball.y,ball.z,ball.vx,ball.vy,previous.x,previous.y,previous.z].every(Number.isFinite))return null;
 const dx=ball.x-previous.x,dy=ball.y-previous.y,dz=ball.z-previous.z;
 if(dx===0&&dy===0&&dz===0)return null;
 let best=null;
 for(const keeper of players){
  if(keeper.team===lastTouchTeam||!(keeper.roster?.position==='GK'||keeper.formationRole==='GK')||![keeper.x,keeper.y].every(Number.isFinite))continue;
  const line=teamDefendsLeft(keeper.team,field)?field.x:field.x+field.w;
  if(Math.abs(keeper.x-line)>90)continue;
  // Find the first instant at which the swept ball center enters the existing
  // provisional reach volume. Closest horizontal approach can occur too late.
  let entry=0,exit=1;
  for(const [start,delta,min,max] of [[previous.x,dx,keeper.x-13,keeper.x+13],[previous.y,dy,keeper.y-18,keeper.y+18],[previous.z,dz,-21,0]]){
   if(delta===0){if(start<min||start>max){entry=2;break;}continue;}
   const a=(min-start)/delta,b=(max-start)/delta;
   entry=Math.max(entry,Math.min(a,b));exit=Math.min(exit,Math.max(a,b));
   if(entry>exit)break;
  }
  if(entry>exit||entry>1||exit<0)continue;
  const t=entry,x=previous.x+t*dx,y=previous.y+t*dy,z=previous.z+t*dz;
  if(!best||t<best.t)best={keeper,t,x,y,z,kind:z>=-9&&Math.hypot(ball.vx,ball.vy)<=6.6?'catch':'parry'};
 }
 return best;
}

// Visual anticipation only; the actual contact still uses the current frame.
// Ten future frames are a provisional browser timing, not a ROM AI constant.
export function predictGoalkeeperShot(ball,players,field,lastTouchTeam){
 if(ball?.actionKind!=='shot'||ball.owner||![ball.x,ball.y,ball.z,ball.vx,ball.vy,ball.vz,ball.gravity].every(Number.isFinite))return null;
 const n=10,future={...ball,x:ball.x+ball.vx*n,y:ball.y+ball.vy*n,z:Math.min(0,ball.z+ball.vz*n+ball.gravity*n*(n+1)/2)};
 return goalkeeperShotContact(ball,future,players,field,lastTouchTeam);
}

export function applyGoalkeeperShotContact(ball,contact){
 const {keeper,kind,x,y,z}=contact;
 if(kind==='catch'){
  Object.assign(ball,{owner:keeper,keeperHeld:true,keeperThrower:null,x:keeper.x,y:keeper.y,z:0,vx:0,vy:0,vz:0,actionKind:null});
 }else{
  const side=y>=keeper.y?1:-1;
  // A contact near the edge can continue toward the end line; central
  // deflections rebound into play. Both outcomes are prototype heuristics.
  const glancing=Math.abs(y-keeper.y)>=10;
  Object.assign(ball,{owner:null,keeperHeld:false,keeperThrower:null,x,y,z,vx:ball.vx*(glancing?0.35:-0.55),vy:ball.vy*0.45+side*2.2,vz:-0.8,actionKind:null});
 }
 return keeper.team;
}

// Provisional retained-ball state after a catch. The visible hand position and
// original release rules are not yet reconstructed.
export function settleHeldGoalkeeperBall(ball){
 if(ball?.keeperHeld!==true)return false;
 const keeper=ball.owner;
 if(!keeper||!(keeper.roster?.position==='GK'||keeper.formationRole==='GK')){ball.keeperHeld=false;return false;}
 Object.assign(ball,{x:keeper.x,y:keeper.y,z:0,vx:0,vy:0,vz:0});
 return true;
}

// Browser approximation: reuse the existing throw-in's pass arc. The ROM's
// goalkeeper release scaling, hand position and animation remain unverified.
export function releaseHeldGoalkeeperPass(ball,actor,direction,speed){
 if(ball?.keeperHeld!==true||ball.owner!==actor||![direction?.x,direction?.y,speed].every(Number.isFinite)||speed<0)throw new RangeError('Invalid goalkeeper release');
 Object.assign(ball,{owner:null,keeperHeld:false,keeperThrower:actor,z:0,vx:direction.x*speed,vy:direction.y*speed,
  vz:BROWSER_THROW_PASS_FLIGHT.vz,gravity:BROWSER_THROW_PASS_FLIGHT.gravity,passRolling:false,actionKind:'keeper_throw'});
}
