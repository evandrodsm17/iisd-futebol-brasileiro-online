// Same 32-bit addition layout as CODE_80:D2B3, in provisional Canvas units.
const FRACTION = 65536;
export function addFixedWords(low, high, deltaLow, deltaHigh) {
  const sum = (low & 65535) + (deltaLow & 65535);
  return { low: sum & 65535, high: ((high & 65535) + (deltaHigh & 65535) + (sum >>> 16)) & 65535 };
}
function encode(value) {
  if (!Number.isFinite(value) || value < -32768 || value >= 32768) throw new RangeError('Position outside signed 16.16 range');
  const raw = Math.round(value * FRACTION) | 0;
  return { low: raw & 65535, high: (raw >>> 16) & 65535 };
}
export function advanceFixed(value, delta) {
  const position = encode(value), motion = encode(delta);
  const result = addFixedWords(position.low, position.high, motion.low, motion.high);
  return ((result.high << 16) | result.low) / FRACTION;
}
export function moveFixed(actor, dx, dy) {
  // Calculate both before committing so invalid input cannot partially move an actor.
  const x = advanceFixed(actor.x, dx), y = advanceFixed(actor.y, dy);
  actor.x = x;
  actor.y = y;
}
