// One free-flight step of the penalty-scene object (8C:9F73 and 8C:9FB9).
// Values are raw 24-bit words; no collision, bounce, stopping or rendering is inferred.
const MASK=0xffffff;
export function advanceNativePenaltyFreeFlight(state,gravity){
 const values=[state?.x,state?.y,state?.z,state?.vx,state?.vy,state?.vz,gravity];
 if(values.some(value=>!Number.isInteger(value)||value<0||value>MASK))throw new RangeError('Invalid 24-bit penalty state');
 return {x:(state.x+state.vx)&MASK,y:(state.y+state.vy)&MASK,z:(state.z+state.vz)&MASK,
         vx:state.vx,vy:state.vy,vz:(state.vz+gravity)&MASK};
}
