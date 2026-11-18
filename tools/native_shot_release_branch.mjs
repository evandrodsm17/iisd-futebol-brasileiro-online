// Narrow translation of the 85:F694 release branch. flags6e is read after
// 80:E3CE; actorWordAfterHelper is read after 80:E7B0, not at entry.
export function nativeShotReleaseBranch(flags6e, actorWordAfterHelper, charge) {
  for (const value of [flags6e, actorWordAfterHelper, charge]) {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff) throw new RangeError('Expected a 16-bit word');
  }
  if (!(flags6e & 0x800)) return { ballType:3, parameter:11, path:'85F871' };
  return { ballType:(actorWordAfterHelper & 1) ? 6 : 5, parameter:charge, path:'85F89B' };
}
