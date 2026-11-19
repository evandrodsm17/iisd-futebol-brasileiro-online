// Entry 8C:944C, before the movement routine. Words and bytes match 65C816.
// The caller decides when the object enters this state and supplies its flags.
export function nativePenaltyKeeperJump({stateFlags,linkedFlags,storedJump,vz}){
 if(!Number.isInteger(stateFlags)||stateFlags<0||stateFlags>0xffff||!Number.isInteger(linkedFlags)||linkedFlags<0||linkedFlags>0xffff||!Number.isInteger(storedJump)||storedJump<0||storedJump>0xffffff||!Number.isInteger(vz)||vz<0||vz>0xffffff)throw new RangeError('Invalid keeper jump state');
 if(linkedFlags&8)return {vz,storedJump,nextState:'waiting',applied:false};
 if(!(stateFlags&8))return {vz,storedJump,nextState:'movement',applied:false};
 return {vz:storedJump,storedJump:storedJump&0xff0000,nextState:'movement',applied:true};
}
