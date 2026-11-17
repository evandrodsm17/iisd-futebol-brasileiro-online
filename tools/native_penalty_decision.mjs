// Experimental translation of 8C:9D18. Inputs are native counters, not web match state.
const LIMITS = [[5, 5, 5, 3, 2], [5, 5, 3, 2, 1]];

export function nativePenaltyDecision({ home, away, side, round }) {
  for (const value of [home, away]) {
    if (!Number.isInteger(value) || value < 0 || value > 127) throw new RangeError('Invalid penalty count');
  }
  if (![0, 2].includes(side) || !Number.isInteger(round) || round < 0 || round > 0xffff) {
    throw new RangeError('Invalid native side or round');
  }
  const difference = home - away;
  if (round >= 5) return side !== 0 && difference !== 0 ? (difference >= 0 ? 0 : 2) : null;
  const limit = LIMITS[side / 2][round] - (side === 0 && difference < 0 ? 1 : 0);
  return Math.abs(difference) >= limit ? (difference >= 0 ? 0 : 2) : null;
}
