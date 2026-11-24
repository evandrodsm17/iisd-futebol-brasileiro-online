"""Summarize recorded input experiments without asserting a general direction mapping."""
import json
from pathlib import Path
from summarize_issd_goalkeeper_direction_search import DIRECTIONS, scan

ROOT = Path(__file__).resolve().parent.parent

def build():
    report = json.loads((ROOT / 'docs/issd-goalkeeper-direction-search.json').read_text(encoding='utf8'))
    runtime = json.loads((ROOT / 'docs/issd-keeper-throw-runtime-audit.json').read_text(encoding='utf8'))
    if report['state_sha256'] != runtime['state_sha256']:
        raise ValueError('Experiments use different saved states')
    grouped = {key: {'long': [], 'turn': []} for key in runtime['directions']}
    if len(report['trials']) != 16:
        raise ValueError('Expected sixteen trials')
    for kind, dirname in [('long', 'keeper-throw-pre110'), ('turn', 'keeper-throw-turns')]:
        recorded = {row['direction']: row for row in report['trials'] if row['kind'] == kind}
        if set(recorded) != set(DIRECTIONS):
            raise ValueError('Incomplete direction experiments')
        for direction in DIRECTIONS:
            row = scan(ROOT / 'analysis' / dirname / direction / 'trial.jsonl', kind)
            if row != recorded[direction]:
                raise ValueError(f'Capture differs from audit: {kind} {direction}')
            orientation = str(row['last_pre_action_direction'])
            expected = [frame['descriptor'] for frame in runtime['directions'].get(orientation, [])]
            if [group['key'][1] for group in row['groups']] != expected or any(group['key'][2] != int(orientation) for group in row['groups']):
                raise ValueError(f'Unmatched descriptors: {kind} {direction}')
            grouped[orientation][kind].append(direction)
    return {'schema': 'issd-keeper-throw-input-evidence/v1', 'state_sha256': report['state_sha256'], 'orientations': grouped}

if __name__ == '__main__':
    output = ROOT / 'dist/data/issd-keeper-throw-input-evidence.json'
    output.write_text(json.dumps(build(), indent=2) + '\n', encoding='utf8')
    print('OK: 16 recorded trials match the five verified descriptors')
