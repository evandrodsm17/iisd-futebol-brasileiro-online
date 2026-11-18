// Experimental translation of 8C:A375. Rectangles are supplied as raw ROM bytes.
const neg = value => (value & 0x80) !== 0;
const byte = value => value & 0xff;

// The native loop tests the record start against end, then reads four bytes.
// Consequently the last read can cross end; preserve the adjacent byte exactly.
export function readNativePenaltyRectangles(bytes, start, end) {
  if (!(bytes instanceof Uint8Array) || !Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > bytes.length) {
    throw new RangeError('Invalid native table bounds');
  }
  const rectangles = [];
  for (let cursor = start; cursor < end; cursor += 4) {
    if (cursor + 4 > bytes.length) throw new RangeError('Missing adjacent native data');
    rectangles.push([...bytes.subarray(cursor, cursor + 4)]);
  }
  return rectangles;
}

export function nativePenaltyHitbox({ x, y, z, otherX, otherY, otherZ, objectFlags, offset, rectangles }) {
  for (const value of [x, y, z, otherX, otherY, otherZ, objectFlags, offset]) {
    if (!Number.isInteger(value) || value < 0 || value > 255) throw new RangeError('Invalid native byte');
  }
  if (!Array.isArray(rectangles) || rectangles.length === 0 || rectangles.some(rect => !Array.isArray(rect) || rect.length !== 4 || rect.some(v => !Number.isInteger(v) || v < 0 || v > 255))) {
    throw new RangeError('Invalid native rectangles');
  }
  let dy = byte(otherY - y + offset);
  if (neg(dy)) dy = byte(-dy);
  if (dy >= 12) return false;
  const dx = byte(otherX - x);
  const dz = byte(otherZ - z);
  for (const [lowX, lowZ, highX, highZ] of rectangles) {
    if (neg(byte(dz - lowZ)) || !neg(byte(dz - highZ - 1))) continue;
    const lower = objectFlags & 0x10 ? byte(-highX) : lowX;
    const upper = objectFlags & 0x10 ? byte(-lowX) : highX;
    if (!neg(byte(dx - lower)) && neg(byte(dx - upper))) return true;
  }
  return false;
}
