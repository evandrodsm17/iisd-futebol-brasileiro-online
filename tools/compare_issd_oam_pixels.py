"""Compare candidate PPU OAM pixels to a captured screenshot (diagnostic only)."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from render_issd_oam_composite import color, decode_tile

SIZES = ((8, 16), (8, 32), (8, 64), (16, 32),
         (16, 64), (32, 64), (16, 32), (16, 32))


def compose(oam, vram, cgram, obsel, slots):
    if len(oam) != 544 or len(vram) != 65536 or len(cgram) != 512:
        raise ValueError('Expected 544-byte OAM, 64 KiB VRAM and 512-byte CGRAM')
    if len(set(slots)) != len(slots) or any(not 0 <= s < 128 for s in slots):
        raise ValueError('Slots must be distinct values from 0 to 127')
    result = {}
    # Lower slot index wins at overlaps, subject to unmodelled PPU priority.
    for slot in sorted(slots, reverse=True):
        x, y, tile, props = oam[4 * slot:4 * slot + 4]
        high = (oam[512 + slot // 4] >> (2 * (slot % 4))) & 3
        if high & 1: x -= 512
        size = SIZES[(obsel >> 5) & 7][high >> 1]
        tile_base = ((obsel & 7) << 9) + ((((obsel & 0x18) + 8) << 5) if props & 1 else 0)
        palette = (props >> 1) & 7
        for sy in range(size):
            for sx in range(size):
                px = size - 1 - sx if props & 0x40 else sx
                py = size - 1 - sy if props & 0x80 else sy
                index = ((tile & 0xF0) | ((tile + (px >> 3)) & 15)) + 16 * (py >> 3)
                value = decode_tile(vram, tile_base + index)[py & 7][px & 7]
                if value and 0 <= x + sx < 256 and 0 <= y + sy < 224:
                    result[(x + sx, y + sy)] = color(cgram, 128 + palette * 16 + value)[:3]
    return result


def compare(pixels, screenshot):
    if screenshot.size != (256, 224): raise ValueError('Expected a native 256x224 screenshot')
    rgb = screenshot.convert('RGB')
    matches = sum(rgb.getpixel(pos) == pixel for pos, pixel in pixels.items())
    return {'candidate_pixels': len(pixels), 'exact_rgb_matches': matches,
            'nonmatching_pixels': len(pixels) - matches}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path)
    p.add_argument('--frame', type=int, required=True)
    p.add_argument('--slots', required=True, help='Comma-separated candidate PPU OAM slots')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); raw = a.trace.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    selected = [r for r in rows if r.get('frame') == a.frame]
    if len(selected) != 1: raise ValueError('Frame missing or ambiguous')
    row = selected[0]
    if not row.get('oam_ppu') or not row.get('cgram_ppu') or not row.get('screenshot'):
        raise ValueError('PPU OAM, PPU CGRAM and screenshot are required')
    root = a.trace.parent
    requested = [int(x) for x in a.slots.split(',')]
    pixels = compose((root / row['oam_ppu']).read_bytes(), (root / row['vram']).read_bytes(),
                     (root / row['cgram_ppu']).read_bytes(), row['obsel'], requested)
    with Image.open(root / row['screenshot']) as shot: measurements = compare(pixels, shot)
    result = {'schema': 'issd-oam-pixel-comparison/v1', 'frame': a.frame, 'slots': requested,
              'source': {'path': a.trace.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()},
              **measurements,
              'limitations': ['Candidate slot attribution and screenshot timing must be established separately.',
                              'Other sprites and backgrounds can occlude pixels; mismatches are not isolated failures.',
                              'SNES priority, blending and colour math are not fully simulated.',
                              'This is not a validated sprite export.']}
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(measurements)


if __name__ == '__main__': main()
