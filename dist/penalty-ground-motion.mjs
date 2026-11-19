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

// 8C:9FA7 tests the post-movement 16-bit position words to select friction
// and bounce. 8C:A056 is called only by particular scripts; the caller chooses it.
export function advanceNativePenaltyMotion(state,gravity,{stopAfter}){
 if(typeof stopAfter!=='boolean')throw new RangeError('Missing stop routine decision');
 const moved=advanceNativePenaltyFreeFlight(state,gravity);
 const height=(moved.z>>>8)&0xffff;
 const grounded=(height&0x8000)===0;
 const result=advanceNativePenaltyGroundStep(state,gravity,{
  frictionX:grounded&&((moved.x>>>8)&0xffff)!==0,
  frictionY:grounded&&((moved.y>>>8)&0xffff)!==0,
  bounce:grounded&&height!==0,
 });
 if(stopAfter){
  const abs16=value=>{const word=value&0xffff;return word&0x8000?(-word)&0xffff:word;};
  if(abs16(result.vz)<0x40&&abs16(result.z>>>8)<2){result.vz=0;result.z=0;}
  if(abs16(result.vx)<0x40&&(result.z>>>8)===0)result.vx=0;
  if(abs16(result.vy)<0x40&&(result.z>>>8)===0)result.vy=0;
 }
 return result;
}
