// Browser prototype decisions. These are not recovered ISSD AI or restart rules.
import {browserContact} from './ball-contact.mjs';
// Prototype policy: hand control to a teammate who actually collects a loose
// ball. The original game's player-selection algorithm is still under study.
export function controlledAfterPickup(controlled, collector, humanTeam=0){
 return collector && collector.team===humanTeam ? collector : controlled;
}
export function planRestart(players,team,kind,x,y,field){
 if(!Array.isArray(players)||![0,1].includes(team)||!['LATERAL','ESCANTEIO','TIRO DE META'].includes(kind)||![x,y,field.x,field.y,field.w,field.h].every(Number.isFinite))throw new RangeError('Reposição inválida');
 const candidates=players.filter(p=>p.team===team);
 if(!candidates.length)throw new RangeError('Equipe sem jogadores');
 const keeper=p=>p.roster?.position==='GK'||p.formationRole==='GK';
 const preferred=kind==='TIRO DE META'?candidates.filter(keeper):candidates.filter(p=>!keeper(p));
 const pool=preferred.length?preferred:candidates;
 let receiver=pool[0],distance=Infinity;
 for(const player of pool){const d=(player.x-x)**2+(player.y-y)**2;if(d<distance){distance=d;receiver=player;}}
 const left=x<field.x+field.w/2,top=y<field.y+field.h/2;
 const direction=kind==='LATERAL'?(top?4:0):kind==='TIRO DE META'?(left?2:6):(top?(left?3:5):(left?1:7));
 return {receiver,direction};
}

export function shouldCpuShoot(actor,controlled,ball,field,now,resetAt){
 if(!actor||actor===controlled||ball.owner!==actor||actor.roster?.position==='GK'||actor.formationRole==='GK'||ball.z!==0||now<resetAt)return false;
 const goalX=actor.team===0?field.x+field.w:field.x;
 return Math.abs(goalX-actor.x)<=175&&Math.abs(actor.y-(field.y+field.h/2))<=field.goalH/2+35;
}

export function shouldCpuClear(actor,controlled,ball,now,ownerSince){
 return !!actor&&actor!==controlled&&ball.owner===actor&&ball.z===0&&
  (actor.roster?.position==='GK'||actor.formationRole==='GK')&&Number.isFinite(now)&&Number.isFinite(ownerSince)&&now-ownerSince>=1000;
}

// Playable browser policy, not recovered ISSD tactics. Prefer a nearby
// outfield teammate with a clear passing lane and some forward progress.
export function chooseCpuPassReceiver(players,actor,controlled,ball,now,ownerSince,resetAt){
 if(!Array.isArray(players)||!actor||actor===controlled||ball.owner!==actor||ball.z!==0||actor.roster?.position==='GK'||actor.formationRole==='GK'||![now,ownerSince,resetAt].every(Number.isFinite)||now<resetAt||now-ownerSince<1800)return null;
 if(![ball.x,ball.y].every(Number.isFinite))return null;
 const forward=actor.team===0?1:-1;
 let best=null,bestScore=-Infinity;
 for(const receiver of players){
  if(receiver===actor||receiver.team!==actor.team||receiver.roster?.position==='GK'||receiver.formationRole==='GK'||![receiver.x,receiver.y].every(Number.isFinite))continue;
  const dx=receiver.x-ball.x,dy=receiver.y-ball.y,distance=Math.hypot(dx,dy);
  if(distance<60||distance>150)continue;
  let blocked=false;
  for(const opponent of players){
   if(opponent.team===actor.team||![opponent.x,opponent.y].every(Number.isFinite))continue;
   const t=((opponent.x-ball.x)*dx+(opponent.y-ball.y)*dy)/(distance*distance);
   if(t>0&&t<1&&Math.hypot(opponent.x-(ball.x+t*dx),opponent.y-(ball.y+t*dy))<18){blocked=true;break;}
  }
  if(blocked)continue;
  const score=forward*dx-distance*.25;
  if(score>bestScore){best=receiver;bestScore=score;}
 }
 return best;
}

export function chooseCpuChallenger(players,controlled,ball,now,ownerSince){
 if(!ball.owner||ball.z!==0||!Number.isFinite(now)||!Number.isFinite(ownerSince)||now-ownerSince<1000)return null;
 let best=null,distance=Infinity;
 for(const player of players){
  if(player===controlled||player.team===ball.owner.team||!browserContact(player,ball))continue;
  const d=Math.hypot(player.x-ball.x,player.y-ball.y);
  if(d<=14&&d<distance){best=player;distance=d;}
 }
 return best;
}
