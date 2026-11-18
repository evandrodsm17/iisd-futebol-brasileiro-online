"""Compare candidate PPU goalkeeper parts against local penalty screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from compare_issd_oam_pixels import compose, compare


def audit(directory):
    manifest_raw = (directory / 'graphics.jsonl').read_bytes()
    rows = [json.loads(line) for line in manifest_raw.splitlines()]
    if rows[0].get('type') != 'capture_start' or rows[-1] != {'type': 'capture_end', 'sequence_count': 5} or any(r.get('type') == 'error' for r in rows):
        raise ValueError('Incomplete graphics capture')
    selectors = [r for r in rows if r.get('type') == 'selector']
    if [r['value'] for r in selectors] != [28, 30, 14, 16, 10]:
        raise ValueError('Unexpected selector sequence')
    first = selectors[0]['frame']
    if [r['frame'] - first for r in selectors] != [0, 3, 7, 11, 26]:
        raise ValueError('Unexpected selector timing')
    candidates = []
    for index in range(1, 6):
        selected = [r for r in rows if r.get('type') == 'graphics' and r['index'] == index and r['delta'] == 2]
        if len(selected) != 1 or not all(selected[0][key] for key in ('vram', 'oam', 'cgram', 'screenshot')):
            raise ValueError('Missing PPU capture')
        record = selected[0]
        stem = record['stem']
        oam, vram, cgram = [(directory / f'{stem}-{kind}.bin').read_bytes() for kind in ('oam', 'vram', 'cgram')]
        screenshot_path = directory / f'{stem}.png'
        slots = []
        for slot in range(128):
            x, y, _, props = oam[4 * slot:4 * slot + 4]
            high = (oam[512 + slot // 4] >> (2 * (slot % 4))) & 3
            if high & 1:
                x -= 512
            # Candidate grouping is deliberately scene-specific, not a native object map.
            if props == 0x3a and 40 <= x < 180 and 35 <= y < 130:
                slots.append(slot)
        pixels = compose(oam, vram, cgram, record['obsel'], slots)
        with Image.open(screenshot_path) as screenshot:
            result = compare(pixels, screenshot)
        if len(slots) < 4 or result['candidate_pixels'] < 100 or result['exact_rgb_matches'] / result['candidate_pixels'] < 0.8:
            raise ValueError('Candidate parts do not meet diagnostic comparison threshold')
        candidates.append({'selector': record['selector'], 'trigger_frame': record['trigger'], 'captured_frame': record['frame'],
                           'slots': slots, 'pixel_comparison': result,
                           'oam_sha256': hashlib.sha256(oam).hexdigest(), 'vram_sha256': hashlib.sha256(vram).hexdigest(),
                           'cgram_sha256': hashlib.sha256(cgram).hexdigest(), 'screenshot_sha256': hashlib.sha256(screenshot_path.read_bytes()).hexdigest()})
    return {'schema': 'issd-penalty-keeper-graphics/v1', 'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
            'candidates': candidates,
            'limits': ['Synthetic match score, clocks and inputs; selector was not forced.',
                       'Slots are scene-specific visual candidates, not proven native actor ownership.',
                       'Pixel mismatches may be caused by occlusion, timing or composition; they are not automatically classified.',
                       'Only five sampled selector transitions and one appearance; sprite timing and other directions are unverified.',
                       'No spritesheet is exported; screenshots and raw PPU data remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['candidates']), 'candidate PPU compositions compared')
