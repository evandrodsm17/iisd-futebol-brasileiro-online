// Isolated model of observed $80:E48D -> $80:E4C7 -> $84:968B path.
// Inputs must come from the original actor state; not wired to gameplay yet.
const FIELD_86_TABLE = Object.freeze([0x0000, 0x0281, 0x0282, 0x0283, 0x8004, 0x0483, 0x0482, 0x0481]);
const CONTROL_TABLE = Object.freeze([0xD0F2, 0xD169, 0xD169, 0xE4CF]);
const SCRIPT_TABLE = Object.freeze([0xD007, 0xD1C5, 0xD16E, 0xE4BF]);
const DPAD_TABLE = Object.freeze([0, 0, 4, 0, 2, 1, 3, 2, 6, 7, 5, 6, 0, 0, 4, 0]);

function word(value, name) {
  if (!Number.isInteger(value) || value < 0 || value > 0xFFFF) throw new RangeError(`${name} must be a 16-bit unsigned integer`);
  return value;
}

export function nativeActionSelection(inputA, actorDirection) {
  const delta = (word(inputA, 'inputA') - word(actorDirection, 'actorDirection')) & 7;
  const field86 = FIELD_86_TABLE[delta];
  // $84:967E takes another path when the field is negative. That path's
  // script selection is not modeled or inferred by this module.
  if (field86 & 0x8000) return Object.freeze({ delta, field86, tableOffset: null, control: null, script: null });
  const tableOffset = (field86 >>> 8) & 7;
  return Object.freeze({ delta, field86, tableOffset,
    control: CONTROL_TABLE[tableOffset / 2], script: SCRIPT_TABLE[tableOffset / 2] });
}

// Only the 80:DD34 held-direction path; callers must first establish that
// the native control flow reached this branch (other branches compute A).
export function nativeHeldDirection(heldWord) {
  const nibble = (word(heldWord, 'heldWord') >>> 8) & 15;
  return nibble === 0 ? null : DPAD_TABLE[nibble];
}
