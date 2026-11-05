// Partial static model of $84:A0D1 -> $80:EED3. The table result supplied by
// the caller is a ROM byte from DATA_81:957F; its index inputs and the call's
// runtime context still need independent capture and calibration.
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
