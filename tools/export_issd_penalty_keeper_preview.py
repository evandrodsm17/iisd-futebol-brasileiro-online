"""Export five locally captured goalkeeper poses after draw-list and pixel checks."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots as draw_slots
from compare_issd_oam_pixels import compose, compare


def export(directory, image_path, report_path):
    raw = (directory / 'graphics.jsonl').read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    if rows[0].get('type') != 'capture_start' or rows[-1] != {'type': 'capture_end', 'sequence_count': 5} or any(r.get('type') == 'error' for r in rows):
        raise ValueError('Incomplete capture')
    selectors = [r for r in rows if r.get('type') == 'selector']
    if [e['value'] for e in selectors] != [28, 30, 14, 16, 10] or len({e['actor'] for e in selectors}) != 1:
        raise ValueError('Unexpected selector sequence')
    frames, evidence = [], []
    for index in range(1, 6):
        selected = [r for r in rows if r.get('type') == 'graphics' and r['index'] == index and r['delta'] == 2]
        if len(selected) != 1 or not all(selected[0][k] for k in ('vram', 'oam', 'cgram', 'screenshot')):
            raise ValueError('Missing PPU data')
        sample = selected[0]
        draw_frame = sample['frame'] - 1
        draws = [r for r in rows if r.get('type') == 'draw_entry' and r['frame'] == draw_frame]
        contexts = [i for i, r in enumerate(draws) if r['object'] == 0x0c00]
        if len(contexts) != 1 or contexts[0] + 1 >= len(draws):
            raise ValueError('Missing or ambiguous draw context')
        pos = contexts[0]
        candidate = draw_slots(draws[pos]['stack'], draws[pos + 1]['stack'])
        stem = sample['stem']
        oam, vram, cgram = [(directory / f'{stem}-{name}.bin').read_bytes() for name in ('oam', 'vram', 'cgram')]
        if not candidate or any(oam[4 * slot + 3] != 0x3a for slot in candidate):
            raise ValueError('Unexpected observed draw parts')
        pixels = compose(oam, vram, cgram, sample['obsel'], candidate)
        with Image.open(directory / f'{stem}.png') as screenshot:
            rgb = screenshot.convert('RGB')
            comparison = compare(pixels, screenshot)
            mismatch = {point for point, color in pixels.items() if rgb.getpixel(point) != color}
            other = compose(oam, vram, cgram, sample['obsel'], [s for s in range(128) if s not in candidate])
            explained = {point for point in mismatch if other.get(point) == rgb.getpixel(point)}
        if len(pixels) < 100 or mismatch != explained:
            raise ValueError('Pixels do not match screenshot or another sprite')
        frames.append(pixels)
        evidence.append({'selector': sample['selector'], 'trigger_frame': sample['trigger'],
                         'draw_frame': draw_frame, 'capture_frame': sample['frame'], 'slots': candidate,
                         'candidate_pixels': comparison['candidate_pixels'], 'direct_matches': comparison['exact_rgb_matches'],
                         'matching_other_sprite_pixels': len(explained)})
    points = [point for frame in frames for point in frame]
    left, top = min(x for x, _ in points), min(y for _, y in points)
    right, bottom = max(x for x, _ in points) + 1, max(y for _, y in points) + 1
    width, height = right - left, bottom - top
    sheet = Image.new('RGBA', (width * len(frames), height))
    for i, frame in enumerate(frames):
        for (x, y), color in frame.items():
            sheet.putpixel((i * width + x - left, y - top), (*color, 255))
    image_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(image_path)
    report = {'schema': 'issd-penalty-keeper-preview/v1', 'capture_manifest_sha256': hashlib.sha256(raw).hexdigest(),
              'image_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(), 'cell_width': width, 'cell_height': height,
              'screen_bounds': [left, top, right, bottom], 'frames': evidence,
              'limits': ['One goalkeeper appearance, direction and five sampled instants.',
                         'Draw context 0c00 uses observed stack ranges; screen matches include pixels matching other sprites.',
                         'The cadence, missing frames, team customization and other directions are not validated.',
                         'Synthetic score, clock and inputs; local extracted graphics are not distributed.']}
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('directory', 'image', 'report'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = export(args.directory, args.image, args.report)
    print('OK:', len(result['frames']), 'local goalkeeper poses exported')
