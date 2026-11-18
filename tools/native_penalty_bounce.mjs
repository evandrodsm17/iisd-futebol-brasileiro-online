// Experimental low-word model of the observed penalty-scene ground bounce.
// Assumes gravity is 0x20, a nonnegative 16-bit velocity, and ground contact.
export function nativePenaltyBounce(position, velocity) {
  for (const value of [position, velocity]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected a 16-bit word');
  }
  if (velocity > 0x7fdf) throw new RangeError('Velocity outside the observed bounce domain');
  const positionAfterMove = (position + velocity) & 0xffff;
  const velocityAfterGravity = (velocity + 0x20) & 0xffff;
  return { position: positionAfterMove & 0xff, velocity: (-Math.floor(velocityAfterGravity / 2)) & 0xffff };
}
