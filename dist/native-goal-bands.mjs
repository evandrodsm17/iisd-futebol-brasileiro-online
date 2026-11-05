// Stadium-indexed words at 81:A833, A843, A853 and A863 (USA ROM).
// These are thresholds for the $2C ball coordinate, not Canvas coordinates.
const bands = Object.freeze([
  [0x0e8, 0x0f0, 0x150, 0x158], [0x108, 0x110, 0x170, 0x178],
  [0x128, 0x130, 0x190, 0x198], [0x108, 0x110, 0x170, 0x178],
  [0x108, 0x110, 0x170, 0x178], [0x0e8, 0x0f0, 0x150, 0x158],
  [0x128, 0x130, 0x190, 0x198], [0x128, 0x130, 0x190, 0x198],
].map(Object.freeze));

export function nativeGoalBands(stadium) {
  if (!Number.isInteger(stadium) || !bands[stadium]) throw new RangeError('Invalid stadium');
  const [outerLow, innerLow, innerHigh, outerHigh] = bands[stadium];
  return {outerLow, innerLow, innerHigh, outerHigh};
}

// Exact unsigned comparisons in CODE_838BAB..838BC8 only. The result is a
// branch, not a goal decision: 838D76 performs further checks and callbacks.
export function nativeGoalBandBranch(stadium, coordinate) {
  if (!Number.isInteger(coordinate) || coordinate < 0 || coordinate > 0xffff) throw new RangeError('Invalid native coordinate');
  const {outerLow, innerLow, innerHigh, outerHigh} = nativeGoalBands(stadium);
  if (coordinate < outerLow || coordinate >= outerHigh) return 'outer';
  if (coordinate < innerLow || coordinate >= innerHigh) return 'edge';
  return 'inner';
}

const isWord = value => Number.isInteger(value) && value >= 0 && value <= 0xffff;

// Branch selection in 83:8C7C..8CBF. Only the selected position and path
// are returned; the helpers on those paths have additional side effects.
export function nativeGoalRearBoundary(x, fieldWidth, velocityXHigh, velocityYHigh) {
  if (![x, fieldWidth, velocityXHigh, velocityYHigh].every(isWord) || fieldWidth > 0x7fff - 0x48) throw new RangeError('Invalid native goal state');
  let target;
  let reflect = false;
  if (x & 0x8000) {
    if (x < 0xffc0 || x >= 0xffd0) return {path:'none', x};
    reflect = !(velocityXHigh & 0x8000) && (velocityYHigh === 0 || !!(velocityYHigh & 0x8000));
    target = reflect ? 0xffc0 : 0xffd0;
  } else {
    if (x < fieldWidth + 0x38 || x >= fieldWidth + 0x48) return {path:'none', x};
    reflect = !!(velocityXHigh & 0x8000) && !(velocityYHigh & 0x8000);
    target = fieldWidth + (reflect ? 0x48 : 0x38);
  }
  // On the reflection path 839011 and 83A900 run; unlike the clamp path,
  // 838D18 is not called and $2A,x is not directly set to target here.
  return reflect ? {path:'reflect', x, target} : {path:'clamp', x:target};
}

// Initial comparisons in 83:8D76..8DA0, before the call to 83:8C7C.
// Inputs are raw 16-bit words; this does not identify an actual goal.
export function nativeGoalEntryBranch(x, height, fieldWidth) {
  if (![x, height, fieldWidth].every(isWord) || fieldWidth > 0x7fff - 0x48) throw new RangeError('Invalid native goal state');
  if (x & 0x8000 ? x < 0xffc1 : x >= fieldWidth + 0x48) return 'outside';
  if (height & 0x8000) {
    if (height < 0xffc0) return 'outside';
    if (height < 0xffc8) return 'height-response';
  }
  return 'continue';
}

// Carry produced by 83:8D61. The caller must pass x *after* 83:8C7C,
// because that helper can change $2A,x. Carry clear alone is not a goal.
export function nativeGoalLineCarry(x, fieldWidth) {
  if (![x, fieldWidth].every(isWord) || fieldWidth > 0x7fff) throw new RangeError('Invalid native goal state');
  const shifted = (x - 4) & 0xffff;
  return shifted & 0x8000 ? shifted >= 0xfff8 : shifted < fieldWidth;
}
