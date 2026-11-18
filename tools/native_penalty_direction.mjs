// Experimental translation of 8C:9E2B; later CPU logic may replace its result.
const INPUT_CODES = [1, 9, 8, 10, 2];

export function nativePenaltyDirection(inputWord) {
  if (!Number.isInteger(inputWord) || inputWord < 0 || inputWord > 0xffff) throw new RangeError('Invalid input word');
  const code = (inputWord >>> 8) & 0x0b;
  let base = INPUT_CODES.lastIndexOf(code);
  if (base < 0) base = 2;
  return { code, base, flagSet: (inputWord & 0x80) !== 0 };
}
