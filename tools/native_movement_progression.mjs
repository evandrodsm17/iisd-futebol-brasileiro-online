// Isolated 16-bit translation of 80:DD9F..DDB5; not integrated into gameplay.
// Restricted subset of 83:C9D7/CA8F: 8-bit inputs and runtime state 0..2.
export function candidateMovementAttributeFields(rawByte, state) {
  if (!Number.isInteger(rawByte) || rawByte < 0 || rawByte > 0x9f || !Number.isInteger(state) || state < 0 || state > 2) throw new RangeError('Outside audited range');
  const delta=state*2-4;
  return {limitLow:Math.max(0,(rawByte&15)+delta), delayLow:Math.min(9,9-(rawByte>>4)-delta)};
}

export function advanceNativeMovementProgression({timer,level,limit,delay}) {
  for (const value of [timer,level,limit,delay]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected 16-bit word');
  }
  const nextTimer=(timer-1)&0xffff;
  if ((nextTimer&0x8000)===0 || level>=limit) return {timer:nextTimer,level,carry:true};
  return {timer:delay&0xff,level:(level+1)&0xffff,carry:false};
}
