// Static dispatch from $84:A346/$84:A35F and the guard at $84:A736.
// This isolates the recovered branch only; it does not infer how $78 is set.
export function nativePlayerReaction({actorAddress,ballOwnerAddress,actorReaction,global78,globalC0}){
 const values=[actorAddress,ballOwnerAddress,actorReaction,global78,globalC0];
 if(values.some(v=>!Number.isInteger(v)||v<0||v>0xffff))throw new RangeError('Dados nativos inválidos');
 if(globalC0!==0)return {route:'blocked',address:0x84a345};
 const type=actorReaction&15;
 const table=[0x84a430,0x84a3ab,0x84a36d,0x84a3b5,0x84a736,0x84a3eb,0x84a7c3];
 if(type>=table.length)return {route:'unknown',type};
 if(type!==4)return {route:'dispatch',type,address:table[type]};
 const alternate=actorAddress===ballOwnerAddress&&(global78&0x8000)!==0;
 return {route:alternate?'alternate':'jump',type,address:alternate?0x84a977:0x84a744};
}
