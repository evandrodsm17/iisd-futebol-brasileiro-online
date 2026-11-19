// Restricted 8C:9196 -> 8C:A6A3 -> 84:E5D1 path. The negative-pointer
// branch is unresolved; the branch decision uses the CPU zero flag, not A.
export function nativeLateralKeeperAnimationGate({counter,scriptPointer}){
 for(const value of [counter,scriptPointer])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation state');
 const nextCounter=(counter-1)&0xffff;
 if(nextCounter===0&&(scriptPointer&0x8000))return {counter:nextCounter,completed:null,nextState:null};
 const completed=nextCounter===0;
 return {counter:nextCounter,completed,nextState:completed?0x91ac:0x9196};
}

// 84:E5DD..E6A3 and the dispatch return. readWord reads bank $82; savedBank
// is the DB restored by PLB, whose zero flag drives the caller's branch.
export function nativePenaltyAnimationReload({scriptPointer,index,tablePointer,variant,savedBank},readWord){
 for(const value of [scriptPointer,index,tablePointer,variant])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation reload state');
 if(savedBank!==undefined&&(!Number.isInteger(savedBank)||savedBank<0||savedBank>255))throw new RangeError('Invalid saved data bank');
 if(!(scriptPointer&0x8000)||typeof readWord!=='function')throw new RangeError('Animation reload requires a negative script pointer and bank reader');
 const read=address=>{const value=readWord(address&0xffff);if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation table word');return value;};
 const timing=read(scriptPointer+(index>>>1));
 const nextPointer=timing&0xff00?scriptPointer:scriptPointer&0x7fff;
 const duration=timing&255;
 const frames=read(tablePointer+((variant<<1)&0xffff));
 const frame=read(frames+index);
 const nextIndex=frame&0x8000?(index+2)&0xffff:0;
 const completed=savedBank===undefined?null:savedBank===0;
 return {counter:duration,scriptPointer:nextPointer,index:nextIndex,frameDescriptor:frame|0x8000,completed};
}

// One call to the animation condition. Inputs must come from the caller;
// unknown DB on a reload propagates as an unknown next state.
export function stepLateralKeeperAnimation(state,readWord){
 const gate=nativeLateralKeeperAnimationGate(state);
 if(gate.completed!==null)return {...state,counter:gate.counter,completed:gate.completed,nextState:gate.nextState};
 const loaded=nativePenaltyAnimationReload(state,readWord);
 return {...state,...loaded,nextState:loaded.completed===null?null:loaded.completed?0x91ac:0x9196};
}

// 8C:92A2 uses the same helper but selects central animation states.
export function stepCentralKeeperAnimation(state,readWord){
 const result=stepLateralKeeperAnimation(state,readWord);
 return {...result,nextState:result.nextState===null?null:result.completed?0x92b8:0x92a2};
}

// Selector read at 8C:952D. readByte addresses the caller's data bank.
export function nativePenaltyAnimationSelector({selector,index,tableAddress},readByte){
 for(const value of [selector,index,tableAddress])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid animation selector state');
 if(typeof readByte!=='function')throw new RangeError('Missing selector table reader');
 const source=(tableAddress-2+index)&0xffff;
 const value=readByte(source);
 if(!Number.isInteger(value)||value<0||value>255)throw new RangeError('Invalid selector table byte');
 const next=value<0x7f?value:selector;
 return {selector:next,changed:next!==selector,source};
}
