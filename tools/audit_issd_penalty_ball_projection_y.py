"""Compare native object drawing coordinates with PPU captures, without assuming alignment."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from compare_issd_oam_pixels import compose, compare
from extract_issd_catalog import EXPECTED_MD5


def delta8(value):
    return ((value + 128) & 255) - 128


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    if len(rom) % 0x8000 or hashlib.md5(rom).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected unheadered ROM')
    expected = bytes.fromhex('c2 20 b5 08 38 e9 04 00 85 18 38 e9 04 00 85 1c b5 0c 18 75 10 38 e9 04 00 85 1a 38 e9 04 00 85 1e')
    if rom[0x1539:0x1539 + len(expected)] != expected:
        raise ValueError('Unexpected projection setup instructions')
    raw = (directory / 'graphics.jsonl').read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    if rows[0].get('type') != 'capture_start' or rows[-1].get('type') != 'capture_end' or any(e.get('type') == 'error' for e in rows):
        raise ValueError('Incomplete capture')
    samples = [e for e in rows if e.get('type') == 'full_graphics']
    if [e['delta'] for e in samples] != list(range(1, 41)):
        raise ValueError('Missing captured frames')
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if not any(e.get('type') == 'synthetic_clock' for e in driver) or not any(e.get('type') == 'synthetic_score' for e in driver) or not any(e.get('type') == 'session_end' for e in driver):
        raise ValueError('Incomplete synthetic driver')
    drawings = {}
    for e in rows:
        if e.get('type') == 'draw_entry':
            drawings.setdefault(e['frame'], []).append(e)
    results = []
    for sample in samples:
        stem = sample['stem']
        oam, vram, cgram = [(directory / f'{stem}-{kind}.bin').read_bytes() for kind in ('oam', 'vram', 'cgram')]
        screenshot_path = directory / f'{stem}.png'
        candidates = []
        for lag in (1, 2, 3, 4):
            draw = drawings.get(sample['frame'] - lag, [])
            indices = [i for i, e in enumerate(draw) if e['object'] == 0x700]
            if len(indices) != 1 or indices[0] + 1 >= len(draw):
                continue
            i = indices[0]
            obj = draw[i]
            selected = slots(obj['stack'], draw[i + 1]['stack'])
            if len(selected) != 1:
                continue
            slot = selected[0]
            x, y, tile, props = oam[4 * slot:4 * slot + 4]
            high = (oam[512 + slot // 4] >> (2 * (slot % 4))) & 3
            if high != 0 or tile != 0xa0 or props != 0x3f or ((sample['obsel'] >> 5) & 7) not in (0, 1, 2):
                continue
            pixels = compose(oam, vram, cgram, sample['obsel'], selected)
            with Image.open(screenshot_path) as image:
                comparison = compare(pixels, image)
            if comparison['candidate_pixels'] != 32 or comparison['exact_rgb_matches'] != 32:
                continue
            native_x, native_y, height = obj['object_x'], obj['object_y'], obj['object_height']
            base_x, base_y = (native_x - 4) & 0xffff, (native_y + height - 4) & 0xffff
            candidates.append({'lag': lag, 'draw_frame': obj['frame'], 'slot': slot,
                               'object_x': native_x, 'object_y': native_y, 'object_height': height,
                               'base_x8': base_x, 'base_y8': base_y, 'oam_x': x, 'oam_y': y,
                               'delta_x': delta8(x - base_x), 'delta_y': delta8(y - base_y)})
        if candidates:
            results.append({'frame': sample['frame'], 'screenshot_sha256': hashlib.sha256(screenshot_path.read_bytes()).hexdigest(),
                            'candidates': candidates})
    if not results:
        raise ValueError('No pixel-validated ball candidates')
    histogram = Counter(str(c['delta_y']) for item in results for c in item['candidates'])
    per_lag = {str(lag): dict(Counter(str(c['delta_y']) for item in results for c in item['candidates'] if c['lag'] == lag)) for lag in (1, 2, 3, 4)}
    two_back = [c for item in results for c in item['candidates'] if c['lag'] == 2]
    if len(results) != 20 or len(two_back) != 20 or any(c['delta_x'] != 0 or c['delta_y'] != -3 for c in two_back):
        raise ValueError('Unexpected two-frame candidate relationship')
    return {'schema': 'issd-penalty-ball-projection-y/v1', 'graphics_sha256': hashlib.sha256(raw).hexdigest(),
            'driver_sha256': hashlib.sha256(driver_raw).hexdigest(), 'rom_offset': '0x1539', 'total_frames': len(samples), 'matched_frames': len(results),
            'candidate_delta_y': dict(histogram), 'candidate_delta_y_by_lag': per_lag, 'samples': results,
            'limits': ['One isolated synthetic match, with score and clock interventions.',
                       'All pixel-compatible draw lags from one through four frames are retained; this does not establish timing.',
                       'The observed -3 offset at lag two could include a per-part descriptor offset; its origin is not established.',
                       'Projection base excludes per-part descriptor offsets, screen clipping and priority.',
                       'Candidate OAM parts can overlap; exact pixel matching alone does not prove unique attribution.',
                       'ROM, screenshots and raw graphics captures remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {result['matched_frames']} pixel-matched frames, candidate Y offsets {result['candidate_delta_y']}")
