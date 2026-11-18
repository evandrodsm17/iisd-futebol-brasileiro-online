// Experimental translation of the native penalty scene's initial vector.
// ROM bytes are supplied locally by the caller and are never bundled here.
import { nativePenaltyShotDirection } from './native_penalty_shot_direction.mjs';

const OFFSETS = [0x28, 0, 0x50];
const BASE = 0x63d7c;

export function nativePenaltyShotVector(rom, variant, inputWord, flags) {
  if (!(rom instanceof Uint8Array) || rom.length < 0x63e03) throw new RangeError('Invalid unheadered ROM');
  if (!Number.isInteger(variant) || variant < 0 || variant >= OFFSETS.length) throw new RangeError('Invalid variant');
  const { code, base, index } = nativePenaltyShotDirection(inputWord, flags);
  // Check the three mode offsets to avoid silently interpreting a different ROM.
  if (OFFSETS.some((v, i) => rom[BASE + i] !== v)) throw new Error('Unexpected penalty table');
  const offset = OFFSETS[variant] + 2 * base;
  const word = address => {
    const n = rom[address] | (rom[address + 1] << 8);
    return n < 0x8000 ? n : n - 0x10000;
  };
  return { code, base, index, tableOffset: offset,
    dx: word(0x63d95 + offset), dy: word(0x63d8b + offset),
    dz: word(((flags & 0x10) !== 0 ? 0x63da9 : 0x63d9f) + offset) };
}
