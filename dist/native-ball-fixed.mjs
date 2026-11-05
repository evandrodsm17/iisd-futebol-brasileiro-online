/** Native 16.16 ball integration and shared integer coordinate translation.
 * Words are unsigned 16-bit representations; return values wrap like the ROM.
 * No conversion to browser-world units or collision handling is implied.
 */
function word(value, label) {
  if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError(`${label} must be a 16-bit word`);
  return value;
}

export function advanceNativeBallAxis(position, velocity, translation = 0) {
  const hi = word(position?.integer, 'position.integer');
  const lo = word(position?.fraction, 'position.fraction');
  const vhi = word(velocity?.integer, 'velocity.integer');
  const vlo = word(velocity?.fraction, 'velocity.fraction');
  const shift = word(translation, 'translation');
  const fractionSum = lo + vlo;
  return {
    integer: (hi + vhi + (fractionSum >= 0x10000 ? 1 : 0) + shift) & 0xffff,
    fraction: fractionSum & 0xffff
  };
}

/** Observed airborne branch only. A positive integer height may take a
 * landing/bounce branch and is intentionally reported as unsupported. */
export function advanceNativeAirborneHeight(position, velocity, acceleration) {
  const nextVelocity = advanceNativeBallAxis(velocity, {integer:0, fraction:word(acceleration, 'acceleration')});
  const nextPosition = advanceNativeBallAxis(position, nextVelocity);
  if (nextPosition.integer !== 0 && (nextPosition.integer & 0x8000) === 0) return null;
  return {position:nextPosition, velocity:nextVelocity};
}
