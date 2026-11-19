import {createPenaltySession,launchPenaltyShot,resolvePenaltyShot,continuePenaltySession} from './penalty-session.mjs';
import {resolveNativePenaltyCrossing} from './penalty-resolution.mjs';

// Reconstruct observed outcomes; an observed_no_goal does not infer its cause.
export function replayPenaltySceneScore(capture){
 if(!capture || !Array.isArray(capture.shots) || !Number.isInteger(capture.goal_frame_index) || capture.goal_frame_index<0 || capture.goal_frame_index>=40)throw new RangeError('Invalid scene capture');
 let session=createPenaltySession(0),lastFrame=-1;const steps=[];
 for(const shot of capture.shots){
  if(shot.launch_frame<=lastFrame || shot.resolved_frame<shot.launch_frame || ![0,2].includes(shot.side) || !Array.isArray(shot.score) || shot.score.length!==2)throw new RangeError('Invalid shot order');
  const team=shot.side/2,before=[...session.shootout.score];
  session=launchPenaltyShot(session,{team,tick:shot.launch_frame,inputWord:shot.input_word,flags:shot.launch_flags});
  if(shot.route==='direct'){
   const result=resolveNativePenaltyCrossing(session,{team,attempt:session.shot.attempt,tick:shot.resolved_frame,flags:shot.resolution_flags,position:shot.position});
   if(result.status!=='resolved')throw new RangeError('Shot is unresolved');
   session=result.session;
  }else if(shot.route==='observed_no_goal'&&shot.scored===false){
   session=resolvePenaltyShot(session,{team,attempt:session.shot.attempt,tick:shot.resolved_frame,scored:false});
  }else throw new RangeError('Unknown captured route');
  if(session.shot.scored!==shot.scored || session.shootout.score.some((value,i)=>value!==shot.score[i]))throw new RangeError('Captured score mismatch');
  steps.push({before,after:[...session.shootout.score],scored:session.shot.scored});
  lastFrame=shot.resolved_frame;session=continuePenaltySession(session);
 }
 if(steps.length!==3 || !steps.at(-1).scored)throw new RangeError('Expected captured goal');
 return {steps,goalFrameIndex:capture.goal_frame_index};
}
