// Individual directions observed for controller 1 in one saved penalty context.
// The caller must select the shooter; results do not establish visual aim or AI.
const OBSERVED_WORDS=Object.freeze({neutral:0,left:0x0200,right:0x0100,up:0x0800,down:0x0400,
 upLeft:0x0a00,upRight:0x0900,downLeft:0x0600,downRight:0x0500});
export function observedPenaltyAimWord(direction){
 if(!Object.hasOwn(OBSERVED_WORDS,direction))throw new RangeError('Penalty direction is not validated');
 return OBSERVED_WORDS[direction];
}
