// Experimental translation of 8C:8E62..8E87 after its three update calls.
export function nativePenaltyDeferredStep({ x, y, height, timer, field28, field29, field32, field33 }) {
  for (const value of [x, y, height, timer, field28, field29, field32, field33]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Invalid native word');
  }
  let nextTimer = timer;
  if (((x | y) & 0xff00) !== 0) {
    nextTimer = (timer - 1) & 0xffff;
    if (nextTimer & 0x8000) return { timer: nextTimer, finalize: true, reason: 'timer' };
  }
  const stopped = (field28 | field29 | field32 | field33 | height) === 0;
  return { timer: nextTimer, finalize: stopped, reason: stopped ? 'fields_zero' : null };
}
