// Narrow, isolated ROM route: 84:BAB7 -> 85:F06E/F088 -> F0D3.
// Caller must already have passed the spatial and preceding state checks.
const ANGLES = Object.freeze([0x00, 0x04, 0x08, 0x18, 0x20, 0x24, 0x28, 0x38]);
function word(value, name) {
  if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError(`${name} must be an unsigned 16-bit word`);
  return value;
}

export function nativeType2Response({ballType, ballAge, actorTeam, referenceTeam, actorFlags, direction, randomWord}) {
  for (const [key,value] of Object.entries({ballType,ballAge,actorTeam,referenceTeam,actorFlags,direction,randomWord})) word(value,key);
  if (ballType !== 2 || ballAge >= 10 || actorTeam === referenceTeam) return { route: 'other', ballType: null };
  // Other +$60 branches have additional logic and are intentionally unresolved.
  if (!(actorFlags & 0x8000)) return { route: 'unresolved', ballType: null };
  if (direction >= ANGLES.length) throw new RangeError('Direction table index outside verified entries');
  return { route: '85:F088', ballType: 1, angle: ANGLES[direction], parameter: (randomWord & 3) + 1 };
}
