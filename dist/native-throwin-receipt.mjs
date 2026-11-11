/** Branch at 84:BAA8, after the game has already reached this contact path.
 * Uses the 65816 CMP negative flag, not a complete possession decision. */
export function nativeReceiptHeightBranch(heightWord) {
  if (!Number.isInteger(heightWord) || heightWord < 0 || heightWord > 0xffff) throw new RangeError('heightWord must be an unsigned 16-bit word');
  return ((heightWord - 0xfff0) & 0x8000) !== 0 ? 'high' : 'low';
}
