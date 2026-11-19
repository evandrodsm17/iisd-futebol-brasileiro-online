"""Compare penalty ball descriptor offsets with pixel-validated OAM candidates."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from audit_issd_penalty_ball_projection_y import audit as audit_projection


def audit(rom_path, roots):
    rom = rom_path.read_bytes()
    sequences = {0x1896: bytes.fromhex('c2 20 a5 1a 18 79 00 40'),
                 0x1924: bytes.fromhex('c2 20 a5 1e 18 79 00 40')}
    for offset, expected in sequences.items():
        if rom[offset:offset+len(expected)] != expected:
            raise ValueError(f'Unexpected part draw instructions at {offset:x}')
    captures = []
    for root, direction in zip(roots, ('Left', 'Right')):
        driver_path, = root.glob('issd-auto-probe-*.jsonl')
        driver = [json.loads(line) for line in driver_path.read_bytes().splitlines()]
        config = [e for e in driver if e.get('type') == 'penalty_direction_config']
        if len(config) != 1 or config[0].get('direction') != direction or config[0].get('controllers') != 'both':
            raise ValueError(f'Unexpected input configuration for {root}')
        base = audit_projection(rom_path, root, strict_reference=False)
        raw = (root/'graphics.jsonl').read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        parts = {}
        for e in rows:
            if e.get('type') == 'ball_part' and e['object'] == 0x700 and e['size'] == 8:
                parts.setdefault(e['frame'], []).append(e)
        results = []
        for sample in base['samples']:
            candidates = []
            for c in sample['candidates']:
                matches = parts.get(c['draw_frame'], [])
                if len(matches) != 1:
                    continue
                part = matches[0]
                expected_x = (c['base_x8'] + part['offset_x']) & 255
                expected_y = (c['base_y8'] + part['offset_y']) & 255
                candidates.append({'lag': c['lag'], 'draw_frame': c['draw_frame'], 'object_x': c['object_x'],
                                   'object_y': c['object_y'], 'object_height': c['object_height'],
                                   'offset_x': part['offset_x'], 'offset_y': part['offset_y'],
                                   'oam_x': c['oam_x'], 'oam_y': c['oam_y'],
                                   'expected_x': expected_x, 'expected_y': expected_y,
                                   'matches_both': expected_x == c['oam_x'] and expected_y == c['oam_y']})
            if candidates:
                results.append({'frame': sample['frame'], 'screenshot_sha256': sample['screenshot_sha256'], 'candidates': candidates})
        if not results:
            raise ValueError(f'No descriptor-linked OAM candidates for {root}')
        counts = {str(lag): sum(c['matches_both'] for item in results for c in item['candidates'] if c['lag'] == lag) for lag in (1,2,3,4)}
        totals = {str(lag): sum(1 for item in results for c in item['candidates'] if c['lag'] == lag) for lag in (1,2,3,4)}
        two_back = [c for item in results for c in item['candidates'] if c['lag'] == 2]
        if len(two_back) != len(results) or not all(c['matches_both'] and c['offset_x'] == 0 and c['offset_y'] == 0xfffd for c in two_back):
            raise ValueError(f'Unexpected two-frame result for {root}')
        captures.append({'name': root.name, 'input_direction': direction, 'controllers': 'both', 'graphics_sha256': hashlib.sha256(raw).hexdigest(),
                         'driver_sha256': base['driver_sha256'], 'matched_frames': len(results),
                         'offsets': dict(Counter(f"{c['offset_x']},{c['offset_y']}" for item in results for c in item['candidates'])),
                         'matched_by_lag': counts, 'candidates_by_lag': totals, 'samples': results})
    return {'schema': 'issd-penalty-directional-projection/v1', 'rom_offsets_checked': [hex(o) for o in sequences],
            'captures': captures,
            'limits': ['Two isolated synthetic captures; Left and Right were applied to both controllers.',
                       'Only 8x8 candidate parts with all opaque pixels matching are included.',
                       'All pixel-compatible lags are retained; matches do not prove universal timing.',
                       'Normal draw path only; other sprite sizes, mirrored paths, priority and occlusion are not covered.',
                       'ROM, screenshots and raw PPU traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom','left','right','output'):
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    result = audit(args.rom,[args.left,args.right])
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for capture in result['captures']:
        print(capture['name'], capture['matched_frames'],capture['matched_by_lag'],capture['candidates_by_lag'],capture['offsets'])
