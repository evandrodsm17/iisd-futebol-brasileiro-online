// Translation of 8C:8DF1..8E24. Flags are supplied at routine entry;
// this function does not decide scoring, movement, collision or flag updates.
export function nativePenaltyPostCrossing({flags,height,vx,vy,vz}) {
 if (![flags,height].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffff) || ![vx,vy,vz].every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffff)) throw new RangeError('Invalid native post-crossing state');
 if ((flags&0x800)!==0 || (height|(vz&0xffff))===0) return {route:'8e30',vx,vy,vz};
 if ((flags&0x20)!==0) return {route:'8e25',vx:0,vy:0,vz};
 return {route:'8e25',vx,vy,vz};
}
