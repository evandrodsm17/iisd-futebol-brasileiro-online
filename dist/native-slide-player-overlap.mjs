import {X_NATIVE_PER_WORLD,Y_NATIVE_PER_WORLD} from './ball-contact.mjs';
// Narrow model of $98:FE8D with DATA_81:D003. Native coordinates only;
// this helper does not implement the later opponent response or web physics.
const word=value=>value&0xffff;
export function nativeSlidePlayerOverlap({actorAddress,linkA6,linkA4,actorFlags,actor,target}){
 const fields=[actorAddress,linkA6,linkA4,actorFlags,actor?.x,actor?.y,actor?.offsetX,actor?.offsetY];
 if(fields.some(n=>!Number.isInteger(n)||n<0||n>0xffff))throw new RangeError('Dados nativos inválidos');
 const targetAddress=linkA6||linkA4;
 if(!targetAddress||targetAddress===actorAddress)return {carry:1,actorFlags,targetAddress,reason:'target'};
 if(!target||[target.x,target.y,target.flags].some(n=>!Number.isInteger(n)||n<0||n>0xffff))throw new RangeError('Alvo nativo inválido');
 if(target.flags&0x0100)return {carry:1,actorFlags,targetAddress,reason:'target_flags'};
 function outside(base,position,offset,targetPosition){const width=base;const delta=word(word(width+position)+offset-targetPosition);return delta>=width*2;}
 if(outside(18,actor.x,actor.offsetX,target.x))return {carry:1,actorFlags,targetAddress,reason:'x'};
 if(outside(12,actor.y,actor.offsetY,target.y))return {carry:1,actorFlags,targetAddress,reason:'y'};
 return {carry:0,actorFlags:actorFlags|0x0020,targetAddress,reason:'overlap'};
}

// Approximate browser adapter: offsets and actor flags are unknown here and
// intentionally set to zero. Field-to-native scale remains provisional.
export function browserSlidePlayerOverlap(actor,target){
 if(![actor?.x,actor?.y,target?.x,target?.y].every(Number.isFinite))return false;
 const dx=target.x-actor.x,dy=target.y-actor.y;
 if(Math.abs(dx)>100||Math.abs(dy)>100)return false;
 return nativeSlidePlayerOverlap({actorAddress:1,linkA6:2,linkA4:0,actorFlags:0,
  actor:{x:0x4000,y:0x4000,offsetX:0,offsetY:0},
  target:{x:0x4000+Math.round(dx*X_NATIVE_PER_WORLD),y:0x4000+Math.round(dy*Y_NATIVE_PER_WORLD),flags:0}}).carry===0;
}
