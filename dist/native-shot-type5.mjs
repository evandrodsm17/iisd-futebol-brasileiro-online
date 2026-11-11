// ROM USA tables 81:A24B / 81:A263, used by 83:9702 for ball type 5.
// Input is the already-selected parameter $0456 (0..11), not a web key press.
// This returns only the initial vertical velocity words, not a full shot.
const high=Object.freeze([0xffff,0xffff,0xffff,0xffff,0xfffe,0xfffe,0xfffe,0xfffe,0xfffe,0xfffd,0xfffd,0xfffd]);
const low=Object.freeze([0xc000,0xc000,0x8000,0x4000,0xc000,0x8000,0x4000,0x0000,0x0000,0xc000,0xc000,0x8000]);
// 81:A233 and 81:A27B use $0456; 81:A293 uses min($12DC & 15, 9).
const field54ByCharge=Object.freeze([0,0,2,2,4,6,8,10,11,12,14,16]);
const field58ByCharge=Object.freeze([0x1000,0x1000,0x1000,0x1000,0x1000,0x1000,0x1c00,0x1c00,0x2000,0x2000,0x2000,0x2000]);
const field54ByContext=Object.freeze([0,0,2,2,4,4,6,6,10,12]);
export function nativeType5InitialVerticalVelocity(parameter){
 if(!Number.isInteger(parameter)||parameter<0||parameter>11)throw new RangeError('Native type-5 parameter must be 0..11');
 return {integer:high[parameter],fraction:low[parameter]};
}

// These are raw initialization fields, not inferred horizontal speed or duration.
export function nativeType5AuxiliaryFields(parameter, contextWord){
 if(!Number.isInteger(parameter)||parameter<0||parameter>11)throw new RangeError('Native type-5 parameter must be 0..11');
 if(!Number.isInteger(contextWord)||contextWord<0||contextWord>0xffff)throw new RangeError('Context word must be 0..65535');
 return {field54:field54ByCharge[parameter]+field54ByContext[Math.min(contextWord&15,9)],field58:field58ByCharge[parameter]};
}
