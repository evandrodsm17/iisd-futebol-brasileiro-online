"""Audit an isolated extended International run; screenshot content needs visual review."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(driver_path, hooks_path, screenshot_path):
    raw, hooks_raw, screenshot = (p.read_bytes() for p in (driver_path, hooks_path, screenshot_path))
    records = [json.loads(line) for line in raw.splitlines()]
    hooks = [json.loads(line) for line in hooks_raw.splitlines()]
    start = [r for r in records if r.get('type') == 'session_start']
    config = [r for r in records if r.get('type') == 'competition_config']
    end = [r for r in records if r.get('type') == 'session_end']
    clocks = [r for r in records if r.get('type') == 'synthetic_clock']
    scores = [r for r in records if r.get('type') == 'synthetic_score']
    if len(start) != 1 or start[0]['target_frames'] != 50000 or len(end) != 1 or end[0]['steps'] != 50000 or end[0]['reason'] != 'frame_limit':
        raise ValueError('Incomplete or unexpected capture')
    if len(config) != 1 or config[0]['menu_mode'] != 'international' or not config[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Unexpected competition configuration')
    if len(scores) != 9 or collections.Counter(r['phase'] for r in clocks) != {0: 9, 1: 9}:
        raise ValueError('Unexpected interventions')
    if [h['site'] for h in hooks] != ['session_start', 'session_end']:
        raise ValueError('Hooks fired or session failed; review required')
    if not screenshot.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Missing screenshot')
    return {'schema': 'issd-international-extended/v1', 'driver_sha256': digest(raw),
            'hook_trace_sha256': digest(hooks_raw), 'screenshot_sha256': digest(screenshot),
            'screenshot_step': 49800, 'final_step': 50000, 'synthetic_clock_writes': clocks,
            'synthetic_score_writes': scores, 'mode_hook_count': 0,
            'limits': ['Screenshot visually reviewed; no automatic image recognition.',
                       'Clock and score were changed synthetically; interventions are not proof of natural match results.',
                       'Negative hook evidence covers only this execution and instrumented routines.',
                       'The router_resolved hook was added after this capture and was not observed here.',
                       'The ROM and raw captures remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('driver', 'hooks', 'screenshot', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.driver, args.hooks, args.screenshot)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: extended capture and synthetic interventions audited')
