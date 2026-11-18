// Experimental translation of 8C:8D79..8DA1, in native unsigned 16-bit units.
export function nativePenaltyGoalGeometry({ x, y, height, flags = 0 }) {
  for (const value of [x, y, height, flags]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Invalid native word');
  }
  if ((flags & 0x0800) !== 0 || y >= 0x005c) return null;
  return x >= 0x0018 && x < 0x00e0 && (height < 0x8000 || height >= 0xffb8);
}
