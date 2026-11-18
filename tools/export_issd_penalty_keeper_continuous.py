"""Export a frame-by-frame local penalty goalkeeper excerpt after PPU checks."""
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
    if rows[0].get('type') != 'capture_start' or rows[-1] != {'type': 'capture_end', 'sequence_count': 5} or any(e.get('type') == 'error' for e in rows):
        raise ValueError('Incomplete capture')
    samples = [e for e in rows if e.get('type') == 'full_graphics']
    if [e['delta'] for e in samples] != list(range(1, 41)):
        raise ValueError('Missing continuous frames')
    frames, evidence = [], []
    for sample in samples:
        if not all(sample[k] for k in ('vram', 'oam', 'cgram', 'screenshot')):
            raise ValueError('Missing graphics data')
        stem = sample['stem']
        oam, vram, cgram = [(directory / f'{stem}-{name}.bin').read_bytes() for name in ('oam', 'vram', 'cgram')]
        candidate = None
        for lag in (1, 2):
            draw_frame = sample['frame'] - lag
            draws = [e for e in rows if e.get('type') == 'draw_entry' and e['frame'] == draw_frame]
            contexts = [i for i, e in enumerate(draws) if e['object'] == 0x0c00]
            if len(contexts) != 1 or contexts[0] + 1 >= len(draws):
                continue
            i = contexts[0]
            selected = draw_slots(draws[i]['stack'], draws[i + 1]['stack'])
            if selected and all(oam[4 * slot + 3] == 0x3a for slot in selected):
                candidate = selected
                break
        if candidate is None:
            raise ValueError(f'No matching draw slots at frame {sample["frame"]}')
        pixels = compose(oam, vram, cgram, sample['obsel'], candidate)
        with Image.open(directory / f'{stem}.png') as screenshot:
            rgb = screenshot.convert('RGB')
            comparison = compare(pixels, screenshot)
            mismatch = {point for point, color in pixels.items() if rgb.getpixel(point) != color}
            others = compose(oam, vram, cgram, sample['obsel'], [slot for slot in range(128) if slot not in candidate])
            explained = {point for point in mismatch if others.get(point) == rgb.getpixel(point)}
        if len(pixels) < 100 or mismatch != explained:
            raise ValueError(f'Unexplained pixels at frame {sample["frame"]}')
        frames.append(pixels)
        evidence.append({'delta': sample['delta'], 'draw_frame': draw_frame, 'capture_frame': sample['frame'],
                         'slots': candidate, 'pixels': len(pixels), 'direct_matches': comparison['exact_rgb_matches'],
                         'matching_other_sprite_pixels': len(explained)})
    points = [point for frame in frames for point in frame]
    left, top = min(x for x, _ in points), min(y for _, y in points)
    right, bottom = max(x for x, _ in points) + 1, max(y for _, y in points) + 1
    width, height = right-left, bottom-top
    sheet = Image.new('RGBA', (width * len(frames), height))
    for index, frame in enumerate(frames):
        for (x, y), color in frame.items():
            sheet.putpixel((index * width + x-left, y-top), (*color, 255))
    image_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(image_path)
    report = {'schema': 'issd-penalty-keeper-continuous/v1', 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
              'image_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(), 'cell_width': width, 'cell_height': height,
              'screen_bounds': [left, top, right, bottom], 'frames': evidence,
              'limits': ['Draw slots were selected by matching properties against one or two preceding frames.',
                         'Forty captured frames are an excerpt, not a proven complete action.',
                         'One direction and appearance; score, clock and inputs were synthetic.',
                         'Matching other sprites explains pixel differences but does not prove priority.',
                         'ROM, raw PPU captures and extracted image remain local.']}
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('directory', 'image', 'report'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = export(args.directory, args.image, args.report)
    print('OK:', len(result['frames']), 'continuous goalkeeper frames exported')
