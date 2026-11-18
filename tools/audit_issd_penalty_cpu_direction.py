"""Audit observed penalty direction changes around the native CPU helper."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    if rom[0x620af:0x620b5] != bytes.fromhex('20 49 a2 ad 08 17') or rom[0x622cb:0x622cf] != bytes.fromhex('8d 08 17 60'):
        raise ValueError('Unexpected CPU-helper call or write')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    endings = [e for e in driver if e.get('type') == 'session_end']
    config = [e for e in driver if e.get('type') == 'penalty_direction_config']
    if len(endings) != 1 or endings[0]['steps'] != 16000 or endings[0]['reason'] != 'frame_limit' or len(config) != 1 or config[0]['direction'] != 'Right' or config[0]['controllers'] != 'p1':
        raise ValueError('Unexpected isolated run')
    before = [e for e in hooks if e['site'] == 'penalty_cpu_before']
    after = [e for e in hooks if e['site'] == 'penalty_cpu_after']
    writes = [e for e in hooks if e['site'] == 'penalty_cpu_write']
    if len(before) != 5 or len(after) != 5 or len(writes) != 1:
        raise ValueError('Unexpected helper calls')
    cases = []
    for start, end in zip(before, after):
        if start['frame'] != end['frame'] or start['d'] != end['d']:
            raise ValueError('Unpaired helper call')
        matching = [e for e in writes if e['frame'] == start['frame'] and e['d'] == start['d']]
        if matching:
            if len(matching) != 1 or matching[0]['direction'] != start['direction'] or matching[0]['a'] != end['direction']:
                raise ValueError('Unexpected helper write')
        elif start['direction'] != end['direction']:
            raise ValueError('Direction changed without observed write')
        cases.append({'before': start, 'after': end, 'writes': matching})
    changed = [c for c in cases if c['before']['direction'] != c['after']['direction']]
    if len(changed) != 1 or changed[0]['before']['direction'] != 2 or changed[0]['after']['direction'] != 0:
        raise ValueError('Unexpected observed change')
    return {'schema': 'issd-penalty-cpu-direction/v1', 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'cases': cases,
            'limits': ['One synthetic shootout and five observed helper calls.',
                       'This captures the helper only, before the subsequent bit-dependent adjustment.',
                       'Random inputs, control roles and statistical probabilities remain unverified.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'CPU helper calls audited')
