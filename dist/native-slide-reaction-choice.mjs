// DATA_81:957F and DATA_81:94C5 from the USA disassembly; this model uses
// values read from the resolved roster record, not assumed player ratings.
const reactionTable=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,1,1,0,0,1,1,0,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1];
const attackerClasses=[0,0,0,1,1,2];
export function nativeSlideReactionTable({attacker30,recordWord,recordNextWord,recordSixthWord,global78}){
 const words=[attacker30,recordWord,recordNextWord,recordSixthWord,global78];
 if(words.some(n=>!Number.isInteger(n)||n<0||n>0xffff))throw new RangeError('Dados nativos inválidos');
 // DATA_81:94C5-1 is indexed by the low byte. Values outside 1..6 access
 // unrelated bytes in the ROM; keep them unresolved rather than extrapolate.
 const slot=attacker30&0xff;
 if(slot<1||slot>attackerClasses.length)return {route:'unresolved_attacker_class'};
 const ability=(recordWord>>4)&15,other=(recordNextWord>>4)&15,detail=recordSixthWord&15;
 const index=(((ability+other)>>1)+detail+attackerClasses[slot-1])*4+(global78&3);
 if(index>=reactionTable.length)return {route:'unresolved_table_index',index};
 return {route:'table',index,tableByte:reactionTable[index]};
}

// Partial static model of $84:A0D1 -> $80:EED3. Call context and runtime
// register inputs must be observed before the model can drive gameplay.
export function nativeSlideReactionChoice({attackerAddress,attacker60,targetAddress,target30,target60,target68,target6c,target6e,foulSetting,global11f9,tableByte}){
 const words=[attackerAddress,attacker60,targetAddress,target30,target60,target68,target6c,target6e,foulSetting,global11f9];
 if(words.some(n=>!Number.isInteger(n)||n<0||n>0xffff)||!Number.isInteger(tableByte)||tableByte<0||tableByte>0xff)throw new RangeError('Dados nativos inválidos');
 const negative=(global11f9&0x8000)!==0;
 // These exits leave the target unchanged and return carry clear.
 if(target68===0&&(target6c&0x100)===0&&foulSetting!==0&&negative)return {route:'early_return',carry:0,target6e};
 if((attacker60&0x4000)===0)return {route:'early_return',carry:0,target6e};
 const flagged=target6e|0x0200;
 // Carry set at the call site writes this fallback reaction and source.
 if(negative||tableByte!==1||(target60&0x0800)!==0)return {route:'fallback',carry:1,target6e:flagged,reaction:0x2002,source:attackerAddress,globalC6:targetAddress};
 return {route:'selected',carry:0,target6e:flagged,reaction:target30===1?0:4,source:attackerAddress,globalC6:targetAddress};
}
