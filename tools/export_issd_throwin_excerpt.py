"""Export a continuous, locally captured throw-in excerpt, without interpolating frames."""
import argparse
import json
from pathlib import Path

from PIL import Image
from audit_issd_throwin_body import audit
from compare_issd_oam_pixels import compose


def export(root, rom, output, first, last):
    if first > last or last - first > 120:
        raise ValueError('Invalid capture range')
    report = audit(root, rom, 0x600, skip_screen_mismatch=True, validate_ball_overlay=True)
    frames = {row['prepared_frame']: row for row in report['frames']}
    poses = {row['frame']: row for row in map(json.loads, (root / 'slide-poses.jsonl').read_text().splitlines())}
    events = [json.loads(line) for line in (root / 'slide-draw.jsonl').read_text().splitlines() if line.strip()]
    if any(f not in frames for f in range(first, last + 1)):
        raise ValueError('Requested range contains missing or unvalidated frames')
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for frame in range(first, last + 1):
        item = frames[frame]
        geometries = [e for e in events if e.get('type') == 'body_geometry' and e['frame'] == frame - 1 and e['object'] == 0x600]
        if len(geometries) != 1:
            raise ValueError('Expected one captured actor origin')
        geometry, record = geometries[0], poses[item['displayed_frame']]
        stem = record['stem']
        pixels = compose((root / (stem + '-ppu.bin')).read_bytes(),
                         (root / (stem + '-vram.bin')).read_bytes(),
                         (root / (stem + '-ppu-cgram.bin')).read_bytes(),
                         record['obsel'], item['slots'] + item['ball_slots'])
        origin_x = geometry['draw_x']
        origin_y = (geometry['draw_y'] + geometry['draw_z']) & 0xffff
        image = Image.new('RGBA', (96, 96))
        for (x, y), color in pixels.items():
            px, py = x - origin_x + 48, y - origin_y + 60
            if not (0 <= px < 96 and 0 <= py < 96):
                raise ValueError('Captured pixel outside the preview canvas')
            image.putpixel((px, py), (*color, 255))
        filename = f'frame-{frame}.png'
        image.save(output / filename)
        result.append({'prepared_frame': frame, 'displayed_frame': item['displayed_frame'],
                       'descriptor': item['descriptor'], 'file': filename,
                       'ball_composited': bool(item['ball_slots'])})
    data = {'schema': 'issd-throwin-excerpt/v1', 'width': 96, 'height': 96,
            'ticks_per_second': 60, 'frames': result,
            'limitations': ['Continuous captured excerpt, not the complete throw.',
                            'Ball is included only when its overlap was validated.',
                            'One scenario, one player, and one uniform; assets remain local.']}
    (output / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return len(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--first', required=True, type=int)
    parser.add_argument('--last', required=True, type=int)
    args = parser.parse_args()
    print('Exported', export(args.capture, args.rom, args.output, args.first, args.last), 'consecutive verified frames')
