"""Export individually validated throw-in body samples for local inspection only."""
import argparse
import json
from pathlib import Path

from PIL import Image
from audit_issd_throwin_body import audit
from compare_issd_oam_pixels import compose


def export(captures, rom, out, lower_captures=None):
    out.mkdir(parents=True, exist_ok=True)
    samples = []
    sets = [('upper', captures)]
    if lower_captures is not None:
        sets.append(('lower', lower_captures))
    for side, captures_root in sets:
      for direction in ('Up', 'Down', 'Left', 'Right'):
        root = captures_root / direction
        report = audit(root, rom, 0x600, skip_screen_mismatch=True)
        poses = {row['frame']: row for row in map(json.loads, (root / 'slide-poses.jsonl').read_text().splitlines())}
        seen = set()
        for item in report['frames']:
            descriptor = item['descriptor']
            if descriptor in seen:
                continue
            seen.add(descriptor)
            record = poses[item['displayed_frame']]
            stem = record['stem']
            pixels = compose((root / (stem + '-ppu.bin')).read_bytes(),
                             (root / (stem + '-vram.bin')).read_bytes(),
                             (root / (stem + '-ppu-cgram.bin')).read_bytes(),
                             record['obsel'], item['slots'])
            if not pixels:
                raise ValueError('No body pixels')
            xmin, xmax = min(x for x, y in pixels), max(x for x, y in pixels)
            ymin, ymax = min(y for x, y in pixels), max(y for x, y in pixels)
            image = Image.new('RGBA', (xmax-xmin+1, ymax-ymin+1))
            for (x, y), color in pixels.items():
                image.putpixel((x-xmin, y-ymin), (*color, 255))
            filename = f'{side}-{direction.lower()}-{descriptor:04x}.png'
            image.save(out / filename)
            samples.append({'side': side, 'input': direction, 'descriptor': descriptor, 'file': filename,
                            'displayed_frame': item['displayed_frame'], 'pixels': len(pixels)})
    manifest = {'schema': 'issd-throwin-body-gallery/v1', 'samples': samples,
                'limitations': ['Individual body samples only; no ball, hair or confirmed animation timing.',
                                'One scenario and uniform; control directions are not generalized.',
                                'ROM-derived graphics must remain local.']}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return len(samples)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--captures', required=True, type=Path)
    p.add_argument('--lower-captures', type=Path, help='opposite-side synthetic scenario captures')
    p.add_argument('--rom', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    print('Exported', export(args.captures, args.rom, args.output, args.lower_captures), 'validated body samples')
