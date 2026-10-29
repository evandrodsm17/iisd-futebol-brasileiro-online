// Provisional Canvas calibration shared by human and AI actors.
export const movementProfiles = Object.freeze({
  walking: Object.freeze({ speed: 1.25, response: 4.5 }),
  running: Object.freeze({ speed: 2, response: 6 }),
});
export function approachMovement(actor, dx, dy, running, dt) {
  const profile = movementProfiles[running ? 'running' : 'walking'];
  const magnitude = Math.hypot(dx, dy) || 1;
  const blend = Math.min(1, dt * profile.response);
  actor.vx += (dx / magnitude * profile.speed - actor.vx) * blend;
  actor.vy += (dy / magnitude * profile.speed - actor.vy) * blend;
}
