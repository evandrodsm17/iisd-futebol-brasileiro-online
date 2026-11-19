import {nativePenaltyGoalGeometryReason} from './penalty-goal-geometry.mjs';
import {resolvePenaltyShot} from './penalty-session.mjs';

// The caller supplies native scene coordinates and the already-advanced contact
// state. A waiting gate never changes the score; collisions remain external.
export function resolveNativePenaltyCrossing(session,{team,attempt,tick,flags,position,deferred}){
 if(!session||session.phase!=='flight'||!session.shot||team!==session.shot.team||attempt!==session.shot.attempt||!Number.isSafeInteger(tick)||tick<session.shot.startedAt||!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid native penalty crossing');
 let reason;
 if(deferred!==undefined){
  if(!deferred||!['applied','resolved'].includes(deferred.phase)||!Number.isSafeInteger(deferred.selectedAt)||deferred.selectedAt<session.shot.startedAt||!Number.isSafeInteger(deferred.actionAt)||deferred.actionAt<=deferred.selectedAt||deferred.actionAt>tick||deferred.flags!==flags||(deferred.checkedAt!==undefined&&(!Number.isSafeInteger(deferred.checkedAt)||deferred.checkedAt>tick)))throw new RangeError('Invalid deferred penalty contact');
  if(deferred.phase==='applied')return {status:'waiting',reason:'deferred',session};
  if(!Number.isSafeInteger(deferred.checkedAt)||deferred.checkedAt<=deferred.actionAt||(flags&0x800)!==0)throw new RangeError('Incomplete deferred penalty contact');
  reason='deferred';
 }else{
  reason=nativePenaltyGoalGeometryReason({...position,flags});
  if(reason==='outside_path')return {status:'waiting',reason,session};
 }
 const scored=reason==='goal_branch';
 return {status:'resolved',reason,session:resolvePenaltyShot(session,{team,attempt,tick,scored})};
}
