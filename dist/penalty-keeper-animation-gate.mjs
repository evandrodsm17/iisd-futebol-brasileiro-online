// Restricted 8C:9196 -> 8C:A6A3 -> 84:E5D1 path. The negative-pointer
// branch is unresolved; the branch decision uses the CPU zero flag, not A.
export function nativeLateralKeeperAnimationGate({counter,scriptPointer}){
 for(const value of [counter,scriptPointer])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation state');
 const nextCounter=(counter-1)&0xffff;
 if(nextCounter===0&&(scriptPointer&0x8000))return {counter:nextCounter,completed:null,nextState:null};
 const completed=nextCounter===0;
 return {counter:nextCounter,completed,nextState:completed?0x91ac:0x9196};
}

// 84:E5DD..E6A3, before the graphics/DMA dispatch. readWord reads bank $82.
// The caller must still obtain the CPU flags produced by that dispatch.
export function nativePenaltyAnimationReload({scriptPointer,index,tablePointer,variant},readWord){
 for(const value of [scriptPointer,index,tablePointer,variant])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation reload state');
 if(!(scriptPointer&0x8000)||typeof readWord!=='function')throw new RangeError('Animation reload requires a negative script pointer and bank reader');
 const read=address=>{const value=readWord(address&0xffff);if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation table word');return value;};
 const timing=read(scriptPointer+(index>>>1));
 const nextPointer=timing&0xff00?scriptPointer:scriptPointer&0x7fff;
 const duration=timing&255;
 const frames=read(tablePointer+((variant<<1)&0xffff));
 const frame=read(frames+index);
 const nextIndex=frame&0x8000?(index+2)&0xffff:0;
 return {counter:duration,scriptPointer:nextPointer,index:nextIndex,frameDescriptor:frame|0x8000,completed:null};
}
