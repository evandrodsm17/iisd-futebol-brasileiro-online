// Experimental translation of 8C:8D79..8DA1, in native unsigned 16-bit units.
// Reasons describe native comparisons; they do not identify screen directions.
export function nativePenaltyGoalGeometryReason({ x, y, height, flags = 0 }) {
  for (const value of [x, y, height, flags]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Invalid native word');
  }
  if ((flags & 0x0800) !== 0 || y >= 0x005c) return 'outside_path';
  if (x < 0x0018 || x >= 0x00e0) return 'x_limit';
  if (height >= 0x8000 && height < 0xffb8) return 'height_limit';
  return 'goal_branch';
}
export function nativePenaltyGoalGeometry(input) {
  const reason = nativePenaltyGoalGeometryReason(input);
  return reason === 'outside_path' ? null : reason === 'goal_branch';
}
