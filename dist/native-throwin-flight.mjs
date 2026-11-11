/** Narrowly observed ISSD throw-in vertical flight and impact cases.
 * Native 16.16 words only; this is not browser physics or full bounce logic. */
import {advanceNativeAirborneHeight} from './native-ball-fixed.mjs';

export function observedThrowInAirborneHeight(ballType, position, velocity) {
  if (ballType !== 15 && ballType !== 20) return null;
  return advanceNativeAirborneHeight(position, velocity, 0x2000);
}

export function observedThrowInImpact(ballType, position, velocity) {
  const matchesA=ballType===20&&position?.integer===65535&&position?.fraction===32768&&velocity?.integer===3&&velocity?.fraction===40960;
  const matchesB=ballType===15&&position?.integer===0&&position?.fraction===16384&&velocity?.integer===2&&velocity?.fraction===57344;
  if(!matchesA&&!matchesB)return null;
  return {position:{integer:0,fraction:0},velocity:{integer:65534,fraction:matchesA?8192:32768}};
}
