// Narrow static model of $84:A08D -> $85:F11A -> $85:FAEA/FAF1.
// This is an analysis helper and is not connected to browser gameplay.
const word=n=>n&0xffff;
function carryOutside(center,width,position,offset,ball){
 const first=word(center+position),sum=first+offset;
 const difference=word((sum&0xffff)-ball-(sum>0xffff?0:1));
 return difference>=width;
}
export function nativeSlideBallGate({timer,actorIsA6,actorFlags,phase,globalFlags,priorContactCarry,actor,ball}){
 const values=[timer,actorFlags,phase,globalFlags,actor?.x,actor?.y,actor?.z,actor?.offsetX,actor?.offsetY,actor?.offsetZ,ball?.x,ball?.y,ball?.z];
 if(values.some(v=>!Number.isInteger(v)||v<0||v>0xffff)||typeof actorIsA6!=='boolean'||typeof priorContactCarry!=='boolean')throw new RangeError('Dados nativos inválidos');
 // $70 is decremented before the signed and unsigned comparisons in A08D.
 const nextTimer=word(timer-1);
 if(actorIsA6||nextTimer&0x8000||nextTimer>=8||(actorFlags&0x0420))return {route:'not_checked',timer:nextTimer,actorFlags};
 // Carry clear invokes F125 first, which can mutate flags, ball and actors.
 if(!priorContactCarry)return {route:'prior_response_unresolved',timer:nextTimer,actorFlags};
 if(phase!==0||(globalFlags&0x8000))return {route:'blocked',timer:nextTimer,actorFlags};
 if(carryOutside(8,16,actor.z,actor.offsetZ,ball.z)||carryOutside(12,24,actor.x,actor.offsetX,ball.x)||carryOutside(8,16,actor.y,actor.offsetY,ball.y))return {route:'outside',timer:nextTimer,actorFlags};
 return {route:'contact',timer:nextTimer,actorFlags:actorFlags|0x0400};
}
