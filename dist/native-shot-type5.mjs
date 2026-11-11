// ROM USA tables 81:A24B / 81:A263, used by 83:9702 for ball type 5.
// Input is the already-selected parameter $0456 (0..11), not a web key press.
// This returns only the initial vertical velocity words, not a full shot.
const high=Object.freeze([0xffff,0xffff,0xffff,0xffff,0xfffe,0xfffe,0xfffe,0xfffe,0xfffe,0xfffd,0xfffd,0xfffd]);
const low=Object.freeze([0xc000,0xc000,0x8000,0x4000,0xc000,0x8000,0x4000,0x0000,0x0000,0xc000,0xc000,0x8000]);
export function nativeType5InitialVerticalVelocity(parameter){
 if(!Number.isInteger(parameter)||parameter<0||parameter>11)throw new RangeError('Native type-5 parameter must be 0..11');
 return {integer:high[parameter],fraction:low[parameter]};
}
