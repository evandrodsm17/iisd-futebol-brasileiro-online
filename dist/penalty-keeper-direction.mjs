import {nativePenaltyDirection} from './penalty-direction.mjs';
// Models the final flag adjustment in 8C:A0A3 after the CPU helper.
// CPU behavior and any interpretation as a screen direction are caller-owned.
export function nativePenaltyKeeperDirection(inputWord,afterCpu){
 if(!Number.isInteger(afterCpu)||afterCpu<0||afterCpu>4)throw new RangeError('Unresolved goalkeeper direction');
 const initial=nativePenaltyDirection(inputWord);
 return {base:initial.base,afterCpu,index:afterCpu+(initial.flagSet?5:0)};
}
