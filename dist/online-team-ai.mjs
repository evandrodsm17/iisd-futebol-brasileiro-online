import {teamDefendsLeft} from './match-sides.mjs';
import {isFallen} from './tackle-reaction.mjs';

// The same simple formation/chase policy used by local play; not native ISSD AI.
export function onlineOutfieldTarget(actor,players,ball,field,tick){
 if(!actor||!Array.isArray(players)||!ball||!field)throw new RangeError('Estado de equipe inválido');
 let closest=null,best=Infinity;
 for(const player of players){
  if(player.team!==actor.team||player.roster?.position==='GK'||player.formationRole==='GK'||isFallen(player,tick))continue;
  const distance=Math.hypot(player.x-ball.x,player.y-ball.y);
  if(distance<best){best=distance;closest=player;}
 }
 const chaser=closest===actor,attacking=ball.owner?.team===actor.team;
 if(ball.owner===actor)return {x:teamDefendsLeft(actor.team,field)?field.x+field.w-60:field.x+60,y:field.y+field.h/2,running:chaser};
 if(chaser&&!attacking)return {x:ball.x,y:ball.y,running:true};
 return {x:actor.homeX+(attacking?(teamDefendsLeft(actor.team,field)?35:-35):0),y:actor.homeY,running:chaser};
}
