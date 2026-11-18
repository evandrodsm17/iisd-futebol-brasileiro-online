// 80:E770..E78E: BPL tests the N flag after a wrapping 16-bit subtraction.
// This describes the flag operation only, not the meaning of the actor fields.
export function nativeShotFieldSide(flags, actorCoordinate, boundary) {
  for (const value of [flags, actorCoordinate, boundary]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected a 16-bit word');
  }
  const negative = (((actorCoordinate - boundary) & 0xffff) & 0x8000) !== 0;
  const set = (flags & 1) ? negative : !negative;
  return { flags: (flags & ~0x800) | (set ? 0x800 : 0), carry: set };
}
