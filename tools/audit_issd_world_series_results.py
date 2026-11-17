"""Check paired World Series runs with opposite synthetic match results."""
import argparse
import hashlib
import json
from pathlib import Path


def read_run(directory, side):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    hook_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    config = [r for r in driver if r.get('type') == 'competition_config']
    ending = [r for r in driver if r.get('type') == 'session_end']
    scores = [r for r in driver if r.get('type') == 'synthetic_score']
    if len(config) != 1 or config[0]['menu_mode'] != 'world_series' or not config[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Wrong route')
    if len(ending) != 1 or ending[0]['steps'] != 6500 or ending[0]['reason'] != 'frame_limit' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete capture')
    if len(scores) != 1 or scores[0].get('side') != side:
        raise ValueError('Unexpected synthetic score')
    writes = [h for h in hooks if h['site'] in ('record_write_before', 'record_write_after')]
    if len(writes) % 2:
        raise ValueError('Unpaired writes')
    pairs = []
    for before, after in zip(writes[::2], writes[1::2]):
        if before['site'] != 'record_write_before' or after['site'] != 'record_write_after' or before['frame'] != after['frame'] or before['index'] != after['index'] or before['a'] != after['value']:
            raise ValueError('Write mismatch')
        pairs.append((before, after))
    active = [(a, b) for a, b in pairs if a['index'] in (a['home_team'], a['away_team'])]
    expected_score = (1, 0) if side == 'home' else (0, 1)
    if len(active) != 2 or any((a['home_score'], a['away_score']) != expected_score or a['value'] != 0 for a, _ in active):
        raise ValueError('Unexpected observed teams or score')
    home, away = active[0][0]['home_team'], active[0][0]['away_team']
    winner, loser = (home, away) if side == 'home' else (away, home)
    changes = {a['index']: b['value'] - a['value'] for a, b in active}
    if home == away or changes != {winner: 256, loser: 1}:
        raise ValueError('Unexpected result updates')
    return {'side': side, 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(hook_raw).hexdigest(), 'synthetic_score': scores[0],
            'team_offsets': {'home': home, 'away': away}, 'matched_writes': [{'before': a, 'after': b} for a, b in active]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('home', type=Path)
    parser.add_argument('away', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = {'schema': 'issd-world-series-results/v1', 'runs': [read_run(args.home, 'home'), read_run(args.away, 'away')],
              'limits': ['Clock and scores were synthetically modified.', 'Only two non-draw outcomes were tested.',
                         'Draws, overflow and other game modes remain unverified.', 'ROM and traces stay local.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: opposite synthetic results updated winner and loser records')
