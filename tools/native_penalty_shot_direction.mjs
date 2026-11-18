// Experimental translation of 8C:9E44 and 8C:9F1C–9F66.
// The returned index is a ROM value, not a verified screen direction.
import { nativePenaltyDirection } from './native_penalty_direction.mjs';

export function nativePenaltyShotDirection(inputWord, flags) {
  if (!Number.isInteger(flags) || flags < 0 || flags > 0xffff) throw new RangeError('Invalid flags');
  const { code, base } = nativePenaltyDirection(inputWord);
  return { code, base, index: base + ((flags & 0x10) === 0 ? 5 : 0) };
}
