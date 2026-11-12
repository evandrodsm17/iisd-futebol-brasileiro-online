// Isolated 16-bit translation of 80:DD9F..DDB5; not integrated into gameplay.
export function advanceNativeMovementProgression({timer,level,limit,delay}) {
  for (const value of [timer,level,limit,delay]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected 16-bit word');
  }
  const nextTimer=(timer-1)&0xffff;
  if ((nextTimer&0x8000)===0 || level>=limit) return {timer:nextTimer,level,carry:true};
  return {timer:delay&0xff,level:(level+1)&0xffff,carry:false};
}
