// Experimental translation of 8C:A295..A2CE, after the earlier control checks.
export function nativePenaltyCpuHistory({ level, gate, random, mask, side, history }) {
  if (!Number.isInteger(level) || level < 0 || level > 0xffff || !Number.isInteger(gate) || gate < 0 || gate > 7 ||
      !Number.isInteger(random) || random < 0 || random > 0xffff || ![3, 7, 15].includes(mask) || ![0, 2].includes(side) ||
      !Array.isArray(history) || history.length !== 16 || history.some(value => !Number.isInteger(value) || value < 0 || value > 0xffff)) {
    throw new RangeError('Invalid native CPU decision data');
  }
  if (gate === 7 || (gate & 3) > level) return { write: false, reason: 'gate' };
  const index = random & mask;
  const value = history[index];
  const offset = (side === 0 ? 0x1760 : 0x1780) + index * 2;
  if (value >= 10) return { write: false, reason: 'history', index, offset, value };
  return { write: true, direction: value >= 5 ? value - 5 : value, index, offset, value };
}

// 8C:A227 writes one word and advances a 32-byte circular offset.
export function nativePenaltyHistoryWrite({ side, cursor, direction, history }) {
  if (![0, 2].includes(side) || !Number.isInteger(cursor) || cursor < 0 || cursor > 30 || cursor % 2 !== 0 ||
      !Number.isInteger(direction) || direction < 0 || direction > 0xffff || !Array.isArray(history) || history.length !== 16 ||
      history.some(value => !Number.isInteger(value) || value < 0 || value > 0xffff)) {
    throw new RangeError('Invalid native history write data');
  }
  const entries = history.slice();
  entries[cursor / 2] = direction;
  return { entries, offset: (side === 0 ? 0x1760 : 0x1780) + cursor, cursor: (cursor + 2) & 0x1f };
}
