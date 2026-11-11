import {decodeOnlineInput} from './online-input.mjs';

// Translate a validated server pair into the engine's team-indexed input map.
// This adapter does not advance the match or decide when a tick is due.
export function decodePairedInputs(message,expectedEpoch,expectedTick,expectedType='input-pair-test'){
 if(!message||typeof message!=='object'||Array.isArray(message)||message.type!==expectedType||typeof expectedEpoch!=='string'||!expectedEpoch||message.epoch!==expectedEpoch||!Number.isSafeInteger(expectedTick)||expectedTick<0||message.tick!==expectedTick||!Array.isArray(message.inputs)||message.inputs.length!==2)return null;
 const first=decodeOnlineInput(message.inputs[0]),second=decodeOnlineInput(message.inputs[1]);
 if(!first||!second||first.tick!==expectedTick||second.tick!==expectedTick)return null;
 return new Map([[0,first.frame],[1,second.frame]]);
}
