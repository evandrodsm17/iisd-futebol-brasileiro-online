import {advanceNativePenaltyKeeper} from './penalty-keeper-motion.mjs';

// Reconstruct only a recorded run. The caller provides observed impulse frames
// and linked flags; neither animation scheduling nor controller input is inferred.
export function replayPenaltyKeeper(capture,impulses){
 if(!capture?.initial||!Array.isArray(capture.samples)||!capture.samples.length||!Array.isArray(impulses))throw new RangeError('Invalid keeper replay');
 const scheduled=new Map();
 for(const event of impulses){
  if(!Number.isSafeInteger(event.frame)||!Number.isInteger(event.vz)||event.vz<0||event.vz>0xffffff||scheduled.has(event.frame))throw new RangeError('Invalid keeper impulse');
  scheduled.set(event.frame,event.vz);
 }
 let state={...capture.initial},previous=null;
 const frames=capture.samples.map(sample=>{
  if(!Number.isSafeInteger(sample.frame)||(previous!==null&&sample.frame!==previous+1))throw new RangeError('Keeper frames must be consecutive');
  previous=sample.frame;
  if(scheduled.has(sample.frame)){state.vz=scheduled.get(sample.frame);scheduled.delete(sample.frame);}
  const before={...state};
  for(const key of ['x','y','z','vx','vy','vz'])if(before[key]!==sample.before?.[key])throw new RangeError('Keeper start differs from recorded state');
  state=advanceNativePenaltyKeeper(state,sample.linked_flags);
  for(const key of ['x','y','z','vx','vy','vz'])if(state[key]!==sample.after?.[key])throw new RangeError('Keeper end differs from recorded state');
  return {frame:sample.frame,before,after:{...state}};
 });
 if(scheduled.size)throw new RangeError('Impulse outside recorded frames');
 return frames;
}
