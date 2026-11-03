// Emulate the ROM's decimal-mode countdown without treating BCD as binary.
export function decrementMatchBcd(value) {
  if (!Number.isInteger(value) || value < 0 || value > 0x9959 ||
      (value & 0xf) > 9 || ((value >> 4) & 0xf) > 5 ||
      ((value >> 8) & 0xf) > 9 || ((value >> 12) & 0xf) > 9) throw new RangeError('Relógio BCD inválido');
  if (value === 0) return 0;
  const seconds = value & 0xff;
  if (seconds) return value - ((seconds & 0x0f) ? 1 : 7);
  const minutes = value >> 8;
  return ((minutes - ((minutes & 0x0f) ? 1 : 7)) << 8) | 0x59;
}
