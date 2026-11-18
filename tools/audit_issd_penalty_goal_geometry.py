"""Compare penalty goal geometry against ROM instructions and captured crossings."""
import argparse
import hashlib
import json
from pathlib import Path


def model(event):
    x, y, height, flags = (event[k] for k in ('x_coord', 'y_coord', 'height', 'shot_flags'))
    if flags & 0x0800 or y >= 0x5c:
        return None
    return 0x18 <= x < 0xe0 and (height < 0x8000 or height >= 0xffb8)


def audit(rom_path, hooks_path):
    rom, raw = rom_path.read_bytes(), hooks_path.read_bytes()
    expected = bytes.fromhex('a5 0c c9 5c 00 b0 e2 ad aa 14 a6 08 e0 18 00 90 37 a6 08 e0 e0 00 b0 30 a6 0c e0 60 00 b0 29 a6 10 10 05 e0 b8 ff 90 20 22 d2 9c 8c')
    if rom[0x60d79:0x60d79 + len(expected)] != expected:
        raise ValueError('Unexpected ROM geometry instructions')
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete hook trace')
    resolved = [(i, e) for i, e in enumerate(hooks) if e['site'] == 'penalty_crossing_resolved']
    if not resolved:
        raise ValueError('No crossing events observed')
    entries = []
    for index, event in resolved:
        # The scoring routine and other hooks run between the two sites, so search
        # backward within the same frame, stopping at a previous resolved crossing.
        scored = False
        for previous in reversed(hooks[:index]):
            if previous.get('frame') != event['frame'] or previous['site'] == 'penalty_crossing_resolved':
                break
            if previous['site'] == 'penalty_goal_branch' and previous['d'] == event['d']:
                scored = True
                break
        expected_result = model(event)
        if expected_result is not None and expected_result != scored:
            raise ValueError(f"Unexpected branch at frame {event['frame']}")
        entries.append({'frame': event['frame'], 'side': event['side'], 'round': event['round'],
                        'x': event['x_coord'], 'y': event['y_coord'], 'height': event['height'], 'goal_branch': scored,
                        'model_applicable': expected_result is not None})
    return {'schema': 'issd-penalty-goal-geometry/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_offset': '0x60d79', 'crossings': entries,
            'limits': ['One synthetic shootout; observed crossings do not cover all geometric boundaries.',
                       'Coordinates are native to this penalty scene, not mapped to web field units.',
                       'Saved shots or other paths may bypass this branch.', 'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', sum(e['model_applicable'] for e in result['crossings']), 'applicable crossings agree with native geometry;',
          sum(not e['model_applicable'] for e in result['crossings']), 'outside this path')
