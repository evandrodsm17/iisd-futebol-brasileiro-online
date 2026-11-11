/** Horizontal launch words for six throw-in cases observed in the USA ROM.
 * Native angle and 16.16 words are not browser coordinates. This is not yet
 * integrated into gameplay; unknown angles/buttons remain unsupported. */
const CASES = Object.freeze({
  A: Object.freeze({3:[3951,1196],8:[1992,1992],13:[597,1907],30:[2899,579]}),
  B: Object.freeze({8:[1992,1992],30:[2899,579]})
});

export function observedThrowInVector(button, angle) {
  const coefficients = CASES[button]?.[angle];
  if (!Number.isInteger(angle) || !coefficients) return null;
  const magnitude = button === 'A' ? 64 : 56;
  const products = [coefficients[0] * magnitude * (((angle + 16) & 63) >= 32 ? -1 : 1),
                    coefficients[1] * magnitude * (angle >= 32 ? -1 : 1)];
  const words = value => {const raw=value>>>0;return {integer:raw>>>16,fraction:raw&0xffff};};
  return {ballType:button === 'A' ? 20 : 15, magnitude,
          velocityX:words(products[0]), velocityY:words(products[1])};
}
