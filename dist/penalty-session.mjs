import {createPenaltyShootout,recordPenaltyKick} from './penalty-shootout.mjs';
import {nativePenaltyShotDirection} from './penalty-direction.mjs';

// A deterministic lifecycle for the browser. It does not infer shot outcomes,
// map browser buttons to native input words, or decide when a shot has ended.
export function createPenaltySession(firstTeam=0){
 return {phase:'aim',shootout:createPenaltyShootout(firstTeam),shot:null};
}
export function launchPenaltyShot(session,{team,tick,inputWord,flags}){
 if(!session||session.phase!=='aim'||team!==session.shootout.nextTeam||!Number.isSafeInteger(tick)||tick<0)throw new RangeError('Invalid penalty launch');
 const direction=nativePenaltyShotDirection(inputWord,flags);
 return {...session,phase:'flight',shot:{team,attempt:session.shootout.attempts.length,startedAt:tick,inputWord,flags,direction}};
}
export function resolvePenaltyShot(session,{team,attempt,tick,scored}){
 if(!session||session.phase!=='flight'||!session.shot||team!==session.shot.team||attempt!==session.shot.attempt||!Number.isSafeInteger(tick)||tick<session.shot.startedAt||typeof scored!=='boolean')throw new RangeError('Invalid penalty resolution');
 const shootout=recordPenaltyKick(session.shootout,team,scored);
 return {...session,phase:'result',shootout,shot:{...session.shot,resolvedAt:tick,scored}};
}
export function continuePenaltySession(session){
 if(!session||session.phase!=='result'||!session.shot)throw new RangeError('Penalty result unavailable');
 return {...session,phase:session.shootout.winner===null?'aim':'finished',shot:null};
}
