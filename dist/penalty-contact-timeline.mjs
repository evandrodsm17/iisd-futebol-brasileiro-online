import {nativePenaltyHitbox,nativePenaltyRectanglesForSelector} from './penalty-hitbox.mjs';
import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
import {advanceNativePenaltyKeeper} from './penalty-keeper-motion.mjs';
const DIRECTIONS=['left','neutral','right'];
// Uses recorded goalkeeper coordinates/selectors only; unrecorded collision
// checks and the motion after contact are not inferred.
export function recordedPenaltyChecks(data,tables,shooter,keeper,motion=null){
 if(data?.schema!=='issd-penalty-contact-timeline/v1'||!Array.isArray(data.cases)||!DIRECTIONS.includes(shooter)||!DIRECTIONS.includes(keeper))throw new RangeError('Invalid recorded contact sequence');
 const matches=data.cases.filter(c=>c.shooter===shooter&&c.keeper===keeper);
 if(matches.length===0)return null;
 if(matches.length!==1||!Array.isArray(matches[0].checks)||!matches[0].checks.length||!Number.isSafeInteger(matches[0].launch_frame))throw new RangeError('Ambiguous contact sequence');
 const recording=matches[0];let previous=recording.launch_frame,state={...recording.initial},contact=false;
 let motionByFrame=null;
 if(motion!==null){
  if(motion?.schema!=='issd-penalty-keeper-motion/v1'||!Array.isArray(motion.captures))throw new RangeError('Invalid keeper motion capture');
  const captures=motion.captures.filter(c=>c.direction===keeper);
  if(captures.length!==1||!Array.isArray(captures[0].samples))throw new RangeError('Ambiguous keeper motion capture');
  // Only independently replayed, matching shooter/keeper directions are paired.
  if(shooter===keeper){motionByFrame=new Map();for(const sample of captures[0].samples){if(!Number.isSafeInteger(sample.frame)||motionByFrame.has(sample.frame))throw new RangeError('Invalid keeper motion sample');motionByFrame.set(sample.frame,sample);}}
 }
 return recording.checks.map(check=>{
  if(contact||!Number.isSafeInteger(check.frame)||check.frame<=previous||check.frame-previous>90||typeof check.hit!=='boolean')throw new RangeError('Invalid recorded check');
  for(let tick=previous;tick<check.frame;tick++)state=advanceNativePenaltyFreeFlight(state,recording.gravity);
  previous=check.frame;contact=check.hit;
  if(!Array.isArray(check.ball_low)||check.ball_low.length!==3||[state.x,state.y,state.z].some((value,index)=>(value&0xffff)!==check.ball_low[index]))throw new RangeError('Ball state differs from captured contact');
  const ball={x:(state.x>>>8)&255,y:(state.y>>>8)&255,z:(state.z>>>8)&255};
  if(!check.geometry||ball.x!==check.geometry.otherX||ball.y!==check.geometry.otherY||ball.z!==check.geometry.otherZ)throw new RangeError('Ball movement differs from captured contact');
  let verified=null;
  if(tables){
   const rectangles=nativePenaltyRectanglesForSelector(tables,check.selector);
   const result=nativePenaltyHitbox({...check.geometry,otherX:ball.x,otherY:ball.y,otherZ:ball.z,rectangles});
   if(result!==check.hit)throw new RangeError('Recorded hitbox result differs');
   verified=true;
  }
  let keeperPosition={x:check.geometry.x,y:check.geometry.y,z:check.geometry.z},keeperSource='recorded';
  const sample=motionByFrame?.get(check.frame);
  if(sample){
   const moved=advanceNativePenaltyKeeper(sample.before,sample.linked_flags);
   const calculated={x:(moved.x>>>8)&255,y:(moved.y>>>8)&255,z:(moved.z>>>8)&255};
   if(Object.keys(calculated).some(key=>calculated[key]!==keeperPosition[key]))throw new RangeError('Keeper motion differs from captured contact');
   keeperPosition=calculated;keeperSource='calculated';
  }
  return {frame:check.frame,selector:check.selector,hit:check.hit,verified,ball,keeper:keeperPosition,keeperSource};
 });
}
