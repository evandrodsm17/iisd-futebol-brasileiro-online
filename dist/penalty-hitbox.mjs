// Translation of 8C:A375. Rectangles are supplied by a local ROM extraction.
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

// Selector is the native byte offset read from the linked object's +14 word.
// No pose or browser direction is inferred from it.
export function nativePenaltyRectanglesForSelector(data,selector){
 if(!data||data.schema!=='issd-penalty-hitbox-tables/v1'||!Array.isArray(data.tables)||!Number.isInteger(selector)||selector<0||selector>30||selector%2!==0)throw new RangeError('Invalid native penalty selector');
 const matches=data.tables.filter(table=>table.selector===selector);
 if(matches.length!==1||!Array.isArray(matches[0].rectangles)||matches[0].rectangles.length===0||matches[0].rectangles.some(rect=>!Array.isArray(rect)||rect.length!==4||rect.some(value=>!Number.isInteger(value)||value<0||value>255)))throw new RangeError('Invalid native penalty table');
 return matches[0].rectangles.map(rect=>[...rect]);
}

// Static gates in 8C:94C6. A selected contact is not necessarily a completed save.
export function nativePenaltyContactDisposition({flags,shotIndex,hit}){
 if(!Number.isInteger(flags)||flags<0||flags>0xffff||!Number.isInteger(shotIndex)||shotIndex<0||shotIndex>0xffff||typeof hit!=='boolean')throw new RangeError('Invalid native contact gate');
 if(flags&0x60)return 'blocked';
 if(!hit)return 'miss';
 if((flags&0x100)&&![1,2,3].includes(shotIndex))return 'excluded';
 return 'selected';
}
