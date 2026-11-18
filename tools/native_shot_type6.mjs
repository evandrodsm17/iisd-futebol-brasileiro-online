// Native type-6 vertical initialization at 83:95D0; input is $0456.
// Uses caller-supplied, unheadered ROM bytes, not browser-world units.
export function nativeType6InitialVertical(rom, parameter) {
  if (!(rom instanceof Uint8Array) || rom.length < 0x9f07) throw new RangeError('Invalid unheadered ROM');
  if (!Number.isInteger(parameter) || parameter < 0 || parameter > 0xffff) throw new RangeError('Invalid native parameter');
  const index=Math.min(parameter,11)*2;
  const word=offset=>rom[offset+index]|(rom[offset+index+1]<<8);
  return {velocity:{integer:word(0x9ebf),fraction:word(0x9ed7)},gravity:word(0x9eef)};
}
