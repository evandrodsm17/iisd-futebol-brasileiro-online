// Base offsets prepared by 80:9539 before descriptor-specific offsets.
// Inputs and outputs are unsigned SNES words; screen visibility is separate.
export function nativeOamProjectionBase({x,y,height}) {
 for(const value of [x,y,height])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid native word');
 const x8=(x-4)&0xffff, y8=(y+height-4)&0xffff;
 return {x8,y8,x16:(x8-4)&0xffff,y16:(y8-4)&0xffff};
}
