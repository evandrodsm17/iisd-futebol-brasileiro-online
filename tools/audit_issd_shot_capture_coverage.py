"""Inventory complete local D007 graphics snapshots without claiming OAM validation."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

REQUIRED = ('vram', 'oam_ppu', 'cgram_ppu', 'screenshot')


def audit(root):
    poses = defaultdict(lambda: {'snapshots': 0, 'complete': 0})
    invalid = 0
    for path in sorted(root.rglob('*graphics.jsonl')):
        with path.open(encoding='utf-8') as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    actor = row.get('actor') or {}
                    if actor.get('animation_script') != 0xd007:
                        continue
                    direction, descriptor = actor['direction'], actor['descriptor']
                    if not isinstance(direction, int) or not 0 <= direction < 8 or not isinstance(descriptor, int):
                        raise ValueError('invalid actor')
                    pose = poses[(direction, descriptor)]
                    pose['snapshots'] += 1
                    if all(isinstance(row.get(key), str) and (path.parent / row[key]).is_file() for key in REQUIRED):
                        pose['complete'] += 1
                except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                    invalid += 1
    return {'schema': 'issd-shot-capture-inventory/v1', 'script': '82:D007',
            'poses': [{'direction': direction, 'descriptor': descriptor, **counts}
                      for (direction, descriptor), counts in sorted(poses.items())],
            'invalid_rows': invalid,
            'limitations': ['File presence only; actor OAM ownership, ROM tiles, timing and pixel composition are not validated.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('capture root does not exist')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit(args.root), indent=2) + '\n', encoding='utf-8')
