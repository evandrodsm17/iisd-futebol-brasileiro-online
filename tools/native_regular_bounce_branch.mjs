// Experimental translation of 83:8941..898C, not complete collision physics.
// The unheadered ROM is supplied locally; the data table is not bundled.
export function nativeRegularVerticalBounce(rom, { ballType, flags, velocity }) {
  if (!(rom instanceof Uint8Array) || rom.length < 0xa8b3) throw new RangeError('Invalid unheadered ROM');
  if (!Number.isInteger(ballType) || ballType < 0 || ballType >= 32) throw new RangeError('Invalid ball type');
  for (const value of [flags, velocity?.integer, velocity?.fraction]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected a 16-bit word');
  }
  const { integer, fraction } = velocity;
  const tableValue = rom[0xa873 + 2 * ballType] | (rom[0xa874 + 2 * ballType] << 8);
  const branch = integer > 0 && integer < 4 && !(flags & 1) && tableValue !== 0 ? 'seven-eighths' : 'half';
  const value = integer * 0x10000 + fraction;
  const result = Math.floor(value / 2) + (branch === 'seven-eighths' ? Math.floor(value / 4) + Math.floor(value / 8) : 0);
  return { branch, velocity: { integer: Math.floor(result / 0x10000), fraction: result % 0x10000 } };
}
