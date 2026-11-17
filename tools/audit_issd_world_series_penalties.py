"""Audit a completed synthetic shootout and subsequent World Series record writes."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(directory):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    raw = driver_path.read_bytes()
    hook_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    driver = [json.loads(line) for line in raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    def typed(name): return [r for r in driver if r.get('type') == name]
    if len(typed('competition_config')) != 1 or typed('competition_config')[0]['menu_mode'] != 'world_series' or not typed('competition_config')[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Wrong competition configuration')
    if len(typed('session_end')) != 1 or typed('session_end')[0]['steps'] != 22000 or typed('session_end')[0]['reason'] != 'frame_limit' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete run')
    scores = typed('synthetic_score')
    if not scores or scores[0]['side'] != 'draw':
        raise ValueError('Missing synthetic draw')
    comparisons = [h for h in hooks if h['site'] == 'result_compare']
    writes = [h for h in hooks if h['site'] in ('record_write_before', 'record_write_after')]
    if len(writes) % 2:
        raise ValueError('Unpaired record writes')
    pairs = []
    for before, after in zip(writes[::2], writes[1::2]):
        if before['site'] != 'record_write_before' or after['site'] != 'record_write_after' or before['frame'] != after['frame'] or before['index'] != after['index'] or before['a'] != after['value']:
            raise ValueError('Record write mismatch')
        if before['index'] in (before['home_team'], before['away_team']):
            pairs.append((before, after))
    if len(pairs) != 2:
        raise ValueError('Expected two team updates')
    before = pairs[0][0]
    if (before['home_score'] & 0x7f, before['away_score'] & 0x7f) != (1, 1) or (before['home_score'], before['away_score']) != (129, 1):
        raise ValueError('Unexpected recorded tied score')
    home_penalty, away_penalty = before['tiebreak_word'] & 255, before['tiebreak_word'] >> 8
    changes = {a['index']: b['value'] - a['value'] for a, b in pairs}
    if (home_penalty, away_penalty) != (8, 7) or changes != {before['home_team']: 256, before['away_team']: 1}:
        raise ValueError('Unexpected winner or record updates')
    if not any(c['penalty_home'] == 8 and c['penalty_away'] == 7 for c in comparisons):
        raise ValueError('Missing result comparison')
    return {'schema': 'issd-world-series-penalties/v1', 'driver_sha256': hashlib.sha256(raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(hook_raw).hexdigest(), 'synthetic_draw': scores[0],
            'synthetic_clock_writes': typed('synthetic_clock'), 'penalty_counts': [home_penalty, away_penalty],
            'result_comparisons': comparisons, 'team_updates': [{'before': a, 'after': b} for a, b in pairs],
            'limits': ['Score, clock and inputs were modified synthetically.',
                       'Only one shootout outcome was observed; timing and other outcomes remain unverified.',
                       'Some checks use temporary counter increments and are not proof of scored penalties.',
                       'The ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(args.directory), indent=2) + '\n', encoding='utf8')
    print('OK: synthetic shootout winner and record updates audited')
