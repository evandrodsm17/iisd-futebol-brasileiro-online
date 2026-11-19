import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
const MASK=0xffffff;
// Caller must supply native branch decisions. This does not detect ground or collisions.
export function advanceNativePenaltyGroundStep(state,gravity,{frictionX,frictionY,bounce}){
 if([frictionX,frictionY,bounce].some(value=>typeof value!=='boolean'))throw new RangeError('Missing native branch decisions');
 const moved=advanceNativePenaltyFreeFlight(state,gravity);
 // The native sign test reads the high byte of the low 16-bit velocity word.
 const slow=value=>(value+((value&0x8000)?8:-8))&MASK;
 if(frictionX)moved.vx=slow(moved.vx);
 if(frictionY)moved.vy=slow(moved.vy);
 if(bounce){
  // Only the observed nonnegative division domain is modelled.
  if(moved.vz>0x7fff)throw new RangeError('Bounce velocity outside observed domain');
  moved.z&=0xff;
  moved.vz=(-Math.floor(moved.vz/2))&MASK;
 }
 return moved;
}
