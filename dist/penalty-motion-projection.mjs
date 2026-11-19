import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
import {advanceNativePenaltyGroundStep} from './penalty-ground-motion.mjs';
import {nativeOamProjectionPart} from './native-oam-projection.mjs';

function projected(state,descriptor){
 const part=nativeOamProjectionPart({...descriptor,x:(state.x>>>8)&0xffff,y:(state.y>>>8)&0xffff,height:(state.z>>>8)&0xffff});
 return {state,oam:{x:part.x&255,y:part.y&255}};
}
// Raw 24-bit native state and descriptor words; callers decide when free flight applies.
export function projectPenaltyAfterFreeFlight(state,gravity,descriptor){
 return projected(advanceNativePenaltyFreeFlight(state,gravity),descriptor);
}
// Only the two captured bounce cases with stationary horizontal velocity.
// Selecting this branch and stopping behavior remains the caller's responsibility.
export function projectPenaltyAfterObservedBounce(state,gravity,descriptor){
 if(state?.vx!==0||state?.vy!==0)throw new RangeError('Bounce outside observed stationary domain');
 return projected(advanceNativePenaltyGroundStep(state,gravity,{frictionX:false,frictionY:false,bounce:true}),descriptor);
}
