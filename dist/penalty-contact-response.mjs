// Raw 24-bit object update in 8C:A500. Caller identifies the native objects
// and decides when contact occurs; no collision or keeper policy is inferred.
const MASK=0xffffff;
export function nativePenaltyContactResponse({target,peerY,source}){
 const values=[target?.y,target?.vx,target?.vy,target?.vz,source?.vx,source?.vz];
 if(values.some(value=>!Number.isInteger(value)||value<0||value>MASK)||!Number.isInteger(peerY)||peerY<0||peerY>0xffff)throw new RangeError('Invalid native contact state');
 const difference=(target.vz-source.vz)&MASK;
 const carry=difference&1;
 // ROR affects the low word only; its carry survives the following INC.
 const rotated=((difference&0xffff)>>>1)|((difference&0x800000)?0x8000:0);
 const upper=((~(((difference>>>16)<<8)|(rotated>>>8)))+carry)&0xffff;
 const low=((~rotated)+1)&0xff;
 return {y:((target.y&0xff)|(((peerY+4)&0xffff)<<8))&MASK,
         vx:(target.vx+source.vx)&MASK,vy:0,vz:((upper<<8)|low)&MASK};
}
