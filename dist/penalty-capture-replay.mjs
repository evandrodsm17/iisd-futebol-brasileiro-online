import {createPenaltySession,launchPenaltyShot,continuePenaltySession} from './penalty-session.mjs';
import {advanceSelectedPenaltyDeferred} from './penalty-contact-sequence.mjs';
import {resolveNativePenaltyCrossing} from './penalty-resolution.mjs';

// Replays recorded native observations; does not simulate a new shot.
export function replayPenaltyCapture(data) {
 if (data?.schema !== 'issd-penalty-replay/v1' || !Array.isArray(data.cases)) throw new RangeError('Invalid penalty capture');
 let session=createPenaltySession(0);
 const steps=[];
 for (const shot of data.cases) {
  const team=shot.side/2;
  session=launchPenaltyShot(session,{team,tick:shot.launch_frame,inputWord:shot.input_word,flags:shot.launch_flags});
  let deferred;
  if (shot.deferred) {
   const {selectedAt,actionAt,flags,checks}=shot.deferred;
   deferred={phase:'applied',selectedAt,actionAt,flags};
   for(const check of checks) deferred=advanceSelectedPenaltyDeferred(deferred,check);
  }
  const result=resolveNativePenaltyCrossing(session,{team,attempt:session.shot.attempt,tick:shot.resolved_frame,flags:shot.resolution_flags,position:shot.position,...(deferred?{deferred}:{})});
  if(result.status!=='resolved'||result.reason!==shot.reason||result.session.shootout.score.some((v,i)=>v!==shot.score[i])) throw new RangeError('Penalty capture does not match result');
  session=result.session;
  steps.push({team,scored:session.shot.scored,score:[...session.shootout.score],reason:result.reason,checks:shot.deferred?.checks.length??0,winner:session.shootout.winner});
  session=continuePenaltySession(session);
 }
 return steps;
}
