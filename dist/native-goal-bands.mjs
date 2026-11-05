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
