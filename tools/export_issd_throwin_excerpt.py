"""Export a continuous, locally captured throw-in excerpt, without interpolating frames."""
import argparse
import json
from pathlib import Path

from PIL import Image
from audit_issd_throwin_body import audit
from analyze_issd_draw_trace import slots
from compare_issd_oam_pixels import compose, compare


def export(root, rom, output, first, last, actor=0x600):
    if first > last or last - first > 120:
        raise ValueError('Invalid capture range')
    report = audit(root, rom, actor, skip_screen_mismatch=True, validate_ball_overlay=True, skip_unresolved=True)
    frames = {row['prepared_frame']: row for row in report['frames']}
    poses = {row['frame']: row for row in map(json.loads, (root / 'slide-poses.jsonl').read_text().splitlines())}
    events = [json.loads(line) for line in (root / 'slide-draw.jsonl').read_text().splitlines() if line.strip()]
    if any(f not in frames for f in range(first, last + 1)):
        raise ValueError('Requested range contains missing or unvalidated frames')
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for frame in range(first, last + 1):
        item = frames[frame]
        geometries = [e for e in events if e.get('type') == 'body_geometry' and e['frame'] == frame - 1 and e['object'] == actor]
        if len(geometries) != 1:
            raise ValueError('Expected one captured actor origin')
        geometry, record = geometries[0], poses[item['displayed_frame']]
        stem = record['stem']
        draw = [e for e in events if not e.get('type') and e['frame'] == frame - 1]
        ball_indices = [i for i, e in enumerate(draw) if e['object'] == 0x400]
        if len(ball_indices) != 1 or ball_indices[0] + 1 >= len(draw):
            raise ValueError('Missing captured ball OAM range')
        i = ball_indices[0]
        ball_slots = slots(draw[i]['stack'], draw[i + 1]['stack'])
        if not ball_slots or set(ball_slots) & set(item['slots']):
            raise ValueError('Invalid ball OAM range')
        oam = (root / (stem + '-ppu.bin')).read_bytes()
        vram = (root / (stem + '-vram.bin')).read_bytes()
        cgram = (root / (stem + '-ppu-cgram.bin')).read_bytes()
        pixels = compose(oam, vram, cgram, record['obsel'], item['slots'] + ball_slots)
        ball_pixels = compose(oam, vram, cgram, record['obsel'], ball_slots)
        if not ball_pixels:
            raise ValueError('Ball is not visible in the captured screen')
        with Image.open(root / (stem + '-screen.png')) as screen:
            comparison = compare(pixels, screen)
        if comparison['nonmatching_pixels']:
            raise ValueError(f'Ball and player differ from screenshot at frame {frame}')
        origin_x = geometry['draw_x']
        origin_y = (geometry['draw_y'] + geometry['draw_z']) & 0xffff
        image = Image.new('RGBA', (160, 128))
        for (x, y), color in pixels.items():
            px, py = x - origin_x + 80, y - origin_y + 84
            if not (0 <= px < 160 and 0 <= py < 128):
                raise ValueError('Captured pixel outside the preview canvas')
            image.putpixel((px, py), (*color, 255))
        filename = f'frame-{frame}.png'
        image.save(output / filename)
        result.append({'prepared_frame': frame, 'displayed_frame': item['displayed_frame'],
                       'descriptor': item['descriptor'], 'file': filename,
                       'ball_composited': True, 'ball_slots': ball_slots})
    data = {'schema': 'issd-throwin-excerpt/v1', 'width': 160, 'height': 128,
            'ticks_per_second': 60, 'frames': result,
            'limitations': ['Continuous captured excerpt, not the complete throw.',
                            'Ball and player are independently located from captured OAM and verified together against the screenshot.',
                            'One scenario, one player, and one uniform; assets remain local.']}
    (output / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return len(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--actor', type=lambda value: int(value,0), default=0x600)
    parser.add_argument('--first', required=True, type=int)
    parser.add_argument('--last', required=True, type=int)
    args = parser.parse_args()
    print('Exported', export(args.capture, args.rom, args.output, args.first, args.last, args.actor), 'consecutive verified frames')
