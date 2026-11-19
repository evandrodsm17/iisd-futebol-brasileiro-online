// Restricted 8C:9196 -> 8C:A6A3 -> 84:E5D1 path. The negative-pointer
// branch is unresolved; the branch decision uses the CPU zero flag, not A.
export function nativeLateralKeeperAnimationGate({counter,scriptPointer}){
 for(const value of [counter,scriptPointer])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation state');
 const nextCounter=(counter-1)&0xffff;
 if(nextCounter===0&&(scriptPointer&0x8000))return {counter:nextCounter,completed:null,nextState:null};
 const completed=nextCounter===0;
 return {counter:nextCounter,completed,nextState:completed?0x91ac:0x9196};
}
