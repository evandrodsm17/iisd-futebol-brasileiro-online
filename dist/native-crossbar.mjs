import { nativeGoalBandBranch } from './native-goal-bands.mjs';

const isWord = n => Number.isInteger(n) && n >= 0 && n <= 0xffff;
const requireWords = values => { if (!values.every(isWord)) throw new RangeError('Invalid native ball state'); };

// Branches 83:8AFF and 83:8B47..8B75, not a complete collision decision.
// Inputs are 16-bit native words; no conversion to browser coordinates occurs.
export function nativeCrossbarCandidate({ stadium, x, y, height, width, velocityXHigh, globalBA }) {
  requireWords([x,y,height,width,velocityXHigh,globalBA]);
  if (nativeGoalBandBranch(stadium,y) !== 'inner') return { response:false, audioCommand:null };
  if (!(height & 0x8000) || height < 0xffc0 || height >= 0xffc8) return { response:false, audioCommand:null };
  let near;
  if (x & 0x8000) near=x>=0xfffc;
  else if (x<4) near=true;
  else { const difference=(x-width)&0xffff, magnitude=difference&0x8000?(-difference)&0xffff:difference;near=magnitude<5; }
  return { response:near, audioCommand:near && velocityXHigh!==0 && globalBA===0 ? 0x2c : null };
}

// 83:8C51..8C78 and 83:90B3..90C2 only, after 83:8D08 has run.
// Returns a pair of words, preserving 16.16 shifts and 16-bit negation.
export function nativeCrossbarHorizontalResponse({ x, vxHigh, vxLow, vyHigh }) {
  requireWords([x,vxHigh,vxLow,vyHigh]);
  const magnitude=(vxHigh&0x8000)?(-vxHigh)&0xffff:vxHigh;
  if (magnitude<2) {
    const high=vyHigh!==0 ? (vyHigh&0x8000?0xffff:1) : (x&0x8000?1:0xffff);
    return { high, low:0 };
  }
  const mask=0xffffffffn,raw=(BigInt(vxHigh)<<16n)|BigInt(vxLow);
  const result=vxHigh&0x8000 ? ((-raw&mask)>>1n) : (-(raw>>1n)&mask);
  return { high:Number(result>>16n), low:Number(result&0xffffn) };
}
