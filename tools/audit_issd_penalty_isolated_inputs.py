"""Compare isolated controller inputs for one native penalty sequence."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(directory, controller, expected, direction='Left'):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    raw, hook_raw = driver_path.read_bytes(), (directory / 'mode-hooks.jsonl').read_bytes()
    driver = [json.loads(line) for line in raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    config = [e for e in driver if e.get('type') == 'penalty_direction_config']
    end = [e for e in driver if e.get('type') == 'session_end']
    if len(config) != 1 or config[0]['direction'] != direction or config[0]['controllers'] != controller or len(end) != 1 or end[0]['steps'] != 10800 or end[0]['reason'] != 'frame_limit':
        raise ValueError('Unexpected run configuration')
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Unexpected hook trace')
    samples = [e for e in driver if e.get('step') in (9300, 9310)]
    if len(samples) != 2:
        raise ValueError('Missing input samples')
    for e in samples:
        if e['phase'] != 9 or (direction in e['input']) != (controller == 'p1') or (direction in e['input_p2']) != (controller == 'p2'):
            raise ValueError('Input isolation failed')
    writes = [e for e in hooks if e['site'] == 'penalty_selector_write' and e['side'] == 0 and e['round'] == 1]
    if [(e['direction_word'], e['value']) for e in writes] != expected:
        raise ValueError('Unexpected selector sequence')
    return {'controller': controller, 'driver_sha256': hashlib.sha256(raw).hexdigest(),
            'hook_sha256': hashlib.sha256(hook_raw).hexdigest(),
            'input_samples': [{k: e[k] for k in ('step', 'phase', 'input', 'input_p2')} for e in samples],
            'selector_changes': writes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('p1', 'p2', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = {'schema': 'issd-penalty-isolated-inputs/v1',
              'runs': [audit(args.p1, 'p1', [(4, 6), (4, 8), (4, 10)]), audit(args.p2, 'p2', [(2, 6), (2, 26), (2, 12)])],
              'limits': ['One direction and one comparable moment; button roles are not conclusively assigned.',
                         'Both controllers still received action pulses; only directional input was isolated.',
                         'Score and clock were synthetic; ROM and raw traces remain local.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: isolated controller direction trials audited')
