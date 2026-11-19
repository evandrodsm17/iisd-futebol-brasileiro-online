// Only individual inputs observed for the shooting controller in the sampled
// penalty context. This does not select a controller or model combinations.
const OBSERVED_WORDS=Object.freeze({neutral:0,left:0x0200,right:0x0100,up:0x0800});
export function observedPenaltyAimWord(direction){
 if(!Object.hasOwn(OBSERVED_WORDS,direction))throw new RangeError('Penalty direction is not validated');
 return OBSERVED_WORDS[direction];
}
