import {ballFootTarget} from './dribble-contact.mjs';
// 84:E8B0's common (+$68 != 0) branch. The Canvas-to-native scale and
// browser possession policy are provisional, not evidence of complete ISSD physics.
export const X_NATIVE_PER_WORLD = 0x740 / 1150;
export const Y_NATIVE_PER_WORLD = 0x280 / 523;
const BASE = 0x4000;
const word = value => value & 0xffff;

function axisCarry(actor, ball, center, width) {
  const sum = actor + center;
  const withBorrow = word((sum & 0xffff) - ball - (sum > 0xffff ? 0 : 1));
  return withBorrow >= width;
}

export function nativeCommonContact(actor, ball) {
  if ([actor.x, actor.y, actor.z, ball.x, ball.y, ball.z].some(v => !Number.isInteger(v) || v < 0 || v > 0xffff)) {
    throw new RangeError('Native contact positions must be unsigned 16-bit integers');
  }
  if (word(actor.z - ball.z) >= 0x18) return false;
  return !axisCarry(actor.x, ball.x, 12, 24) && !axisCarry(actor.y, ball.y, 8, 16);
}

export function browserContact(actor, ball) {
  if (![actor.x, actor.y, ball.x, ball.y, ball.z].every(Number.isFinite)) return false;
  if (Math.abs(ball.x - actor.x) > 100 || Math.abs(ball.y - actor.y) > 100 || Math.abs(ball.z) > 100) return false;
  // Anchor both coordinates in the same safe part of the 16-bit space. Only
  // relative distance is used; the field projection has not been calibrated.
  const nativeBall = {
    x: word(BASE + Math.round((ball.x - actor.x) * X_NATIVE_PER_WORLD)),
    y: word(BASE + Math.round((ball.y - actor.y) * Y_NATIVE_PER_WORLD)),
    z: word(Math.round(ball.z * Y_NATIVE_PER_WORLD)),
  };
  return nativeCommonContact({x: BASE, y: BASE, z: 0}, nativeBall);
}

export function closestContactPlayer(players, ball) {
  let closest = null, bestDistance = Infinity;
  for (const player of players) {
    if (!browserContact(player, ball)) continue;
    const distance = (player.x - ball.x) ** 2 + (player.y - ball.y) ** 2;
    if (distance < bestDistance) { closest = player; bestDistance = distance; }
  }
  return closest;
}

// The browser's 260 ms re-pickup delay is still provisional. It prevents the
// releasing side from immediately recovering the ball, but must not block an
// opposing player who reaches a loose grounded ball during that window.
export function pickupPlayer(players, ball, lastTouchTeam, elapsedMs) {
  if (!Number.isFinite(elapsedMs) && elapsedMs !== Infinity) return null;
  const candidates = elapsedMs > 260 ? players : players.filter(player => player.team !== lastTouchTeam);
  return closestContactPlayer(candidates, ball);
}

// Browser approximation for an airborne throw-in. The contact test is based on
// the ROM's common branch; scaling, cooldown and candidate ordering are provisional.
export function collectAirborneThrow(players,ball,lastTouchTeam,elapsedMs){
 if(ball.owner || ball.actionKind!=='throw_in' || !(ball.z<0))return null;
 const receiver=pickupPlayer(players,ball,lastTouchTeam,elapsedMs);
 if(!receiver)return null;
 Object.assign(ball,ballFootTarget(receiver),{owner:receiver,z:0,vx:0,vy:0,vz:0,actionKind:null,passRolling:false});
 return receiver;
}
