"""Correlate native penalty object X with visible OAM positions in saved captures."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from compare_issd_oam_pixels import compose, compare


def audit(directory):
    captures = []
    for name in ('world-penalty-graphics-full', 'world-penalty-graphics-Left', 'world-penalty-graphics-Right'):
        root = directory / name
        manifest_raw = (root / 'graphics.jsonl').read_bytes()
        rows = [json.loads(line) for line in manifest_raw.splitlines()]
        if rows[0].get('type') != 'capture_start' or rows[-1].get('type') != 'capture_end' or any(row.get('type') == 'error' for row in rows):
            raise ValueError('Incomplete graphics trace')
        driver_path, = root.glob('issd-auto-probe-*.jsonl')
        driver_raw = driver_path.read_bytes()
        driver = [json.loads(line) for line in driver_raw.splitlines()]
        if not any(e.get('type') == 'synthetic_clock' for e in driver) or not any(e.get('type') == 'synthetic_score' for e in driver):
            raise ValueError('Missing synthetic capture interventions')
        hook_raw = (root / 'mode-hooks.jsonl').read_bytes()
        hooks = [json.loads(line) for line in hook_raw.splitlines()]
        if not any(e.get('site') == 'penalty_crossing_resolved' and e.get('d') == 0x700 for e in hooks):
            raise ValueError('No resolution for the captured native object')
        frames = {row['frame']: row for row in driver if 'actors' in row}
        draws = {}
        for event in rows:
            if event.get('type') == 'draw_entry':
                draws.setdefault(event['frame'], []).append(event)
        results, eligible = [], 0
        for sample in (row for row in rows if row.get('type') == 'full_graphics' and row['frame'] in frames):
            eligible += 1
            entries = draws.get(sample['frame'] - 1, [])
            indexes = [i for i, e in enumerate(entries) if e['object'] == 0x700]
            if len(indexes) != 1 or indexes[0] + 1 >= len(entries):
                continue
            i = indexes[0]
            selected = slots(entries[i]['stack'], entries[i + 1]['stack'])
            stem = sample['stem']
            oam, vram, cgram = [(root / f'{stem}-{kind}.bin').read_bytes() for kind in ('oam', 'vram', 'cgram')]
            if len(selected) != 1:
                continue
            slot = selected[0]
            x, y, tile, props = oam[slot * 4:slot * 4 + 4]
            high = (oam[512 + slot // 4] >> (2 * (slot % 4))) & 3
            # Limit inference to the consistently observed 8x8 ball graphic.
            if high != 0 or tile != 0xa0 or props != 0x3f or ((sample['obsel'] >> 5) & 7) not in (0, 1, 2):
                continue
            pixels = compose(oam, vram, cgram, sample['obsel'], selected)
            screenshot_path = root / f'{stem}.png'
            with Image.open(screenshot_path) as screenshot:
                comparison = compare(pixels, screenshot)
            if comparison['candidate_pixels'] != 32 or comparison['exact_rgb_matches'] != 32:
                continue
            actors = [actor for actor in frames[sample['frame']]['actors'] if actor['address'] == 0x700]
            if len(actors) != 1:
                raise ValueError('Missing native object sample')
            actor = actors[0]
            results.append({'frame': sample['frame'], 'draw_frame': sample['frame'] - 1, 'slot': slot,
                            'native_x': actor['x'], 'native_y': actor['y'], 'oam_x': x, 'oam_y': y,
                            'center_x': x + 4, 'center_minus_native_x': x + 4 - actor['x'],
                            'matching_pixels': 32, 'screenshot_sha256': hashlib.sha256(screenshot_path.read_bytes()).hexdigest()})
        captures.append({'name': name, 'graphics_sha256': hashlib.sha256(manifest_raw).hexdigest(),
                         'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
                         'hooks_sha256': hashlib.sha256(hook_raw).hexdigest(), 'aligned_samples': eligible, 'matches': results})
    observations = [entry for capture in captures for entry in capture['matches']]
    differences = Counter(str(entry['center_minus_native_x']) for entry in observations)
    if len(observations) != 7 or differences != {'0': 6, '2': 1}:
        raise ValueError('Unexpected coordinate observations')
    return {'schema': 'issd-penalty-ball-screen-x/v1', 'captures': captures, 'differences': dict(differences),
            'limits': ['Three isolated recordings with synthetic scores, clocks and automatic input.',
                       'Only frame-aligned samples with one validated 8x8 OAM part and all 32 opaque pixels matching are included.',
                       'Draw-list attribution assumes one-frame lag; sample timing or later movement may explain differences, but the cause is unproven.',
                       'The +4 center applies only to this 8x8 OAM part; other poses and sizes are not covered.',
                       'Y is not calibrated; depth, height, occlusion and camera behavior remain unresolved.',
                       'ROM, raw PPU captures and screenshots remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: 7 validated ball OAM samples; 6 exact X centers and 1 offset by 2 pixels')
