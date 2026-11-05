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

/** The single observed type-2 bounce branch: positive horizontal velocities,
 * first impact, weather value 1 and the captured vertical speed of 1.5 native units.
 * Other conditions return null until their branches are validated. */
export function observedType2Bounce({ballType, weather, flags, parameter, velocityX, velocityY, impactVelocity}) {
  if (ballType !== 2 || weather !== 1 || flags !== 0 || !Number.isInteger(parameter) || parameter < 0 || parameter > 0xffff) return null;
  const zhi = word(impactVelocity?.integer, 'impactVelocity.integer');
  const zlo = word(impactVelocity?.fraction, 'impactVelocity.fraction');
  const xhi = word(velocityX?.integer, 'velocityX.integer'), xlo = word(velocityX?.fraction, 'velocityX.fraction');
  const yhi = word(velocityY?.integer, 'velocityY.integer'), ylo = word(velocityY?.fraction, 'velocityY.fraction');
  if (zhi !== 1 || zlo !== 32768 || xhi >= 0x8000 || yhi >= 0x8000) return null;
  const reducedZ = Math.floor((zhi * 65536 + zlo) / 2);
  if (reducedZ < 0x6000) return null;
  const reversedZ = (0x100000000 - reducedZ) % 0x100000000;
  const reduceHorizontal = (hi, lo) => {
    const magnitude = hi * 65536 + lo;
    const reduced = Math.floor(magnitude / 2) + Math.floor(magnitude / 4);
    return {integer:Math.floor(reduced / 65536), fraction:reduced % 65536};
  };
  return {
    positionZ:{integer:0, fraction:0},
    velocityZ:{integer:Math.floor(reversedZ / 65536), fraction:reversedZ % 65536},
    velocityX:reduceHorizontal(xhi, xlo), velocityY:reduceHorizontal(yhi, ylo),
    parameter:Math.floor(parameter / 2) + Math.floor(parameter / 4), flags:1
  };
}
