"""Audit one isolated synthetic World Series route and its sorter hooks."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def audit(directory):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    raw = driver_path.read_bytes()
    hooks_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    records = [json.loads(line) for line in raw.splitlines()]
    hooks = [json.loads(line) for line in hooks_raw.splitlines()]
    one = lambda name: [r for r in records if r.get('type') == name]
    if len(one('session_start')) != 1 or one('session_start')[0]['target_frames'] != 16000 or len(one('session_end')) != 1 or one('session_end')[0]['steps'] != 16000 or one('session_end')[0]['reason'] != 'frame_limit':
        raise ValueError('Incomplete capture')
    if len(one('competition_config')) != 1 or one('competition_config')[0]['menu_mode'] != 'world_series' or not one('competition_config')[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Unexpected route')
    if len(one('synthetic_score')) != 4 or len(one('synthetic_clock')) != 7:
        raise ValueError('Unexpected synthetic interventions')
    counts = collections.Counter(h['site'] for h in hooks)
    expected = {'session_start': 1, 'session_end': 1, 'router': 3, 'router_resolved': 3, 'ranking_start': 6, 'ranking_end': 6, 'ranking_store': 216}
    if counts != expected or hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Unexpected instrumented calls')
    groups = []
    for start in [h for h in hooks if h['site'] == 'ranking_start']:
        frame = start['frame']
        stores = [h for h in hooks if h['site'] == 'ranking_store' and h['frame'] == frame]
        ends = [h for h in hooks if h['site'] == 'ranking_end' and h['frame'] == frame]
        if len(ends) != 1 or [s['x'] for s in stores] != list(range(0, 72, 2)) or sorted(s['y'] for s in stores) != list(range(0, 72, 2)):
            raise ValueError('Unexpected sorter output')
        groups.append({'frame': frame, 'direct_page': start['d'], 'indices': [s['y'] for s in stores]})
    sha = lambda b: hashlib.sha256(b).hexdigest()
    images = {}
    for step in (1200, 4200, 6000):
        data = (directory / (driver_path.stem + '-' + str(step) + '.png')).read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Missing screenshot')
        images[str(step)] = sha(data)
    return {'schema': 'issd-world-series-route/v1', 'driver_sha256': sha(raw), 'hook_trace_sha256': sha(hooks_raw),
            'screenshots_sha256_by_step': images, 'hook_counts': dict(counts), 'sorter_groups': groups,
            'router_observations': [h for h in hooks if h['site'] in ('router', 'router_resolved')],
            'synthetic_clock_writes': one('synthetic_clock'), 'synthetic_score_writes': one('synthetic_score'),
            'limits': ['Screenshots visually inspected, not automatically classified.',
                       'Clock, score and menu inputs were modified in the isolated run.',
                       'Sorting permutations do not establish scoring, tie-breaking or natural match results.',
                       'Router hooks deduplicate state signatures and are not call counts.',
                       'Raw captures and ROM stay local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.directory), indent=2) + '\n', encoding='utf8')
    print('OK: World Series route and six sorter permutations audited')
