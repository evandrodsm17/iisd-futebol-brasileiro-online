"""Compare two isolated penalty runs with opposite directional inputs."""
import argparse
import hashlib
import json
from pathlib import Path


def run(directory, direction, expected):
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    hooks_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    hooks = [json.loads(line) for line in hooks_raw.splitlines()]
    configs = [e for e in driver if e.get('type') == 'penalty_direction_config']
    ends = [e for e in driver if e.get('type') == 'session_end']
    if len(configs) != 1 or configs[0]['direction'] != direction or configs[0]['controllers'] != 'both' or len(ends) != 1 or ends[0]['steps'] != 10800 or ends[0]['reason'] != 'frame_limit':
        raise ValueError('Unexpected route or incomplete run')
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Unexpected hook trace')
    samples = [e for e in driver if e.get('step') in (9300, 9310)]
    if len(samples) != 2 or any(e['phase'] != 9 or direction not in e['input'] or direction not in e['input_p2'] for e in samples):
        raise ValueError('Requested inputs were not observed in the penalty scene')
    writes = [e for e in hooks if e['site'] == 'penalty_selector_write' and e['side'] == 0 and e['round'] == 1]
    if [(e['direction_word'], e['value']) for e in writes] != expected:
        raise ValueError('Unexpected observed selector changes')
    return {'direction': direction, 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(hooks_raw).hexdigest(), 'input_samples': [{k: e[k] for k in ('step', 'phase', 'input', 'input_p2')} for e in samples],
            'selector_changes': writes}


def graphics(directory, expected):
    raw = (directory / 'graphics.jsonl').read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    if rows[0].get('type') != 'capture_start' or rows[-1] != {'type': 'capture_end', 'sequence_count': 3} or any(e.get('type') == 'error' for e in rows):
        raise ValueError('Incomplete direction graphics')
    changes = [e for e in rows if e.get('type') == 'selector']
    if [e['value'] for e in changes] != expected:
        raise ValueError('Unexpected graphics selector sequence')
    frames = [e for e in rows if e.get('type') == 'full_graphics']
    if [e['delta'] for e in frames] != list(range(1, 41)) or not all(all(e[k] for k in ('vram', 'oam', 'cgram', 'screenshot')) for e in frames):
        raise ValueError('Incomplete graphics frames')
    image = (directory / 'full-20.png').read_bytes()
    if not image.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Missing screenshot')
    return {'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'selector_changes': changes,
            'image_delta': 20, 'image_sha256': hashlib.sha256(image).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('left', 'right', 'graphics_left', 'graphics_right', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = {'schema': 'issd-penalty-direction-inputs/v1',
              'runs': [run(args.left, 'Left', [(4, 6), (4, 8), (4, 10)]), run(args.right, 'Right', [(2, 6), (2, 26), (2, 12)])],
              'graphics': [graphics(args.graphics_left, [6, 8, 10]), graphics(args.graphics_right, [6, 26, 12])],
              'limits': ['Both controllers received the direction, so goalkeeper and shooter effects are not isolated.',
                         'Clock, score and input were synthetic; no direct memory direction override was used.',
                         'Only one comparable moment per run; screenshot content was reviewed visually, not classified automatically.',
                         'ROM and raw captures stay local.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: opposite input runs and selector changes audited')
