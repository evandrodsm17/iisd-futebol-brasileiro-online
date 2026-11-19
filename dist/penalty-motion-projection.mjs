import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
import {nativeOamProjectionPart} from './native-oam-projection.mjs';

// Raw 24-bit native state and descriptor words; callers decide when free flight applies.
export function projectPenaltyAfterFreeFlight(state,gravity,descriptor){
 const next=advanceNativePenaltyFreeFlight(state,gravity);
 const part=nativeOamProjectionPart({...descriptor,x:(next.x>>>8)&0xffff,y:(next.y>>>8)&0xffff,height:(next.z>>>8)&0xffff});
 return {state:next,oam:{x:part.x&255,y:part.y&255}};
}
