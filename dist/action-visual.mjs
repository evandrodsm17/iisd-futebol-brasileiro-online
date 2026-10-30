// Game rendering adapter for OAM action candidates captured from the SNES.
// D007 = BigKick. D100 = LowKick art (used as a PROVISIONAL pass visual).
// Timings are visual preview values, not verified complete native durations.
export const ACTION_SPRITE_STATUS = 'experimental-oam';
export const ACTIONS = Object.freeze({
  shot: Object.freeze({ script: 'D007', directions: [0, 2, 3, 4, 6, 7], durations: [2, 1, 1, 1, 1, 4] }),
  pass: Object.freeze({ script: 'D100', directions: [0, 2, 3, 4, 6], durations: [1, 1, 1, 1, 1, 4] }),
});
// Screen-direction -> action ROM direction: locomotive direction converter is
// separate; a missing captured action direction uses the nearest OBSERVED pose.
// Never manufacture a new sprite by mirroring.
export const ACTION_ROM_BY_SCREEN = Object.freeze([6, 7, 0, 0, 2, 3, 4, 6]);
export const ACTION_FRAME = Object.freeze({ width: 96, height: 96, anchorX: 48, anchorY: 68 });
export const ACTION_SLOWDOWN = 3; // visual readability; NOT a recovered ROM constant
export function directionForAction(kind, screenDirection) {
  const def = ACTIONS[kind];
  if (!def) return null;
  const candidate = ACTION_ROM_BY_SCREEN[screenDirection] ?? 0;
  if (def.directions.includes(candidate)) return candidate;
  // D100 direction 7 has not been captured, use observed direction 6.
  return candidate === 7 ? 6 : def.directions[0];
}
export function durationInTicks(kind) {
  const action = ACTIONS[kind];
  return action ? action.durations.reduce((sum, x) => sum + x, 0) * ACTION_SLOWDOWN : 0;
}
export function actionFrame(kind, elapsedTicks) {
  const action = ACTIONS[kind];
  if (!action || !Number.isFinite(elapsedTicks) || elapsedTicks < 0) return null;
  let ticks = Math.floor(elapsedTicks);
  for (let i = 0; i < action.durations.length; i++) {
    const remaining = action.durations[i] * ACTION_SLOWDOWN;
    if (ticks < remaining) return i;
    ticks -= remaining;
  }
  return null; // action finished; revert to the original locomotion sprite
}
export function actionAssetPath(kind, direction) {
  if (!ACTIONS[kind]?.directions.includes(direction)) return null;
  return './assets/issd/actions/' + ACTIONS[kind].script + '/direction-' + direction + '.png';
}
