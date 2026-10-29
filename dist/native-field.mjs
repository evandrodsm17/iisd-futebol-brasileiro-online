// DATA_81:EC47, verified against the local USA ROM. Canvas scale is provisional.
export const nativeDimensions = Object.freeze([
  [0x700, 0x240], [0x740, 0x280], [0x7c0, 0x2c0], [0x800, 0x280],
  [0x780, 0x280], [0x780, 0x240], [0x700, 0x2c0], [0x880, 0x2c0],
].map(Object.freeze));

export function fieldDimensions(id) {
  if (!Number.isInteger(id) || !nativeDimensions[id]) throw new RangeError('Invalid stadium');
  const [width, height] = nativeDimensions[id];
  return { w: 1150 * width / 0x740, h: 523 * height / 0x280 };
}

export function resizeField(field, id, entities) {
  const next = fieldDimensions(id);
  for (const entity of entities) {
    for (const [key, origin, before, after] of [
      ['x', field.x, field.w, next.w], ['homeX', field.x, field.w, next.w],
      ['y', field.y, field.h, next.h], ['homeY', field.y, field.h, next.h],
    ]) {
      if (Number.isFinite(entity[key])) entity[key] = origin + (entity[key] - origin) * after / before;
    }
  }
  Object.assign(field, next);
}
