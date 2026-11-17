"""Audit an isolated drawn World Series run; images require visual inspection."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(directory):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    hook_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    screenshot = (directory / (driver_path.stem + '-9000.png')).read_bytes()
    records = [json.loads(line) for line in driver_raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    by_type = lambda name: [r for r in records if r.get('type') == name]
    config, end = by_type('competition_config'), by_type('session_end')
    scores, clocks = by_type('synthetic_score'), by_type('synthetic_clock')
    if len(config) != 1 or config[0]['menu_mode'] != 'world_series' or not config[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Wrong competition mode')
    if len(end) != 1 or end[0]['steps'] != 10000 or end[0]['reason'] != 'frame_limit' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete capture')
    if len(scores) != 1 or scores[0]['side'] != 'draw' or scores[0]['before_home'] != 0 or scores[0]['before_away'] != 0:
        raise ValueError('Unexpected score intervention')
    if [r['phase'] for r in clocks] != [0, 1, 2, 3] or [r['before'] for r in clocks] != [1105, 1280, 768, 768]:
        raise ValueError('Unexpected clock interventions')
    if any(h['site'].startswith('record_write_') or h['site'] == 'ranking_start' for h in hooks):
        raise ValueError('Result or ranking routine ran; additional review required')
    if not screenshot.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Missing screenshot')
    sha = lambda data: hashlib.sha256(data).hexdigest()
    return {'schema': 'issd-world-series-draw/v1', 'driver_sha256': sha(driver_raw), 'hooks_sha256': sha(hook_raw),
            'screenshot_step': 9000, 'screenshot_sha256': sha(screenshot), 'synthetic_score': scores[0],
            'synthetic_clock_writes': clocks, 'record_updates_observed': 0,
            'limits': ['The penalty scene was identified by visual inspection, not image recognition.',
                       'Both score and clocks were synthetically modified.',
                       'The penalty shootout did not complete within this capture.',
                       'No result updates were observed during this route; other paths may differ.',
                       'ROM and raw captures remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.directory), indent=2) + '\n', encoding='utf8')
    print('OK: drawn synthetic route with four clock phases audited')
