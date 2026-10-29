// Fixed simulation cadence; long stalls are discarded rather than fast-forwarded.
export function createSimulationClock(update) {
  const step = 1 / 60;
  let remainder = 0;
  return {
    advance(seconds) {
      if (!Number.isFinite(seconds) || seconds < 0) return 0;
      remainder += Math.min(seconds, 0.1);
      let ticks = 0;
      while (remainder + 1e-12 >= step && ticks < 6) {
        update(step);
        remainder = Math.max(0, remainder - step);
        ticks++;
      }
      return ticks;
    },
    reset() { remainder = 0; },
  };
}
