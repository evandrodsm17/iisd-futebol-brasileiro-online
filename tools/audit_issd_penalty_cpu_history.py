"""Audit observed random-gate and history selections in the penalty CPU helper."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    expected = bytes.fromhex('22 19 84 85 c9 07 00 f0 30 29 03 00 cd 54 1e f0 02 b0 26 22 f3 83 85 2d 00 00 0a ae 40 14 18 7f a5 be 8c aa bf 00 00 81 c9 0a 00 b0 0c c9 05 00 90 04 38 e9 05 00 8d 08 17 60')
    if rom[0x62295:0x62295 + len(expected)] != expected or rom[0x63ea5:0x63ea9] != bytes.fromhex('60 17 80 17'):
        raise ValueError('Unexpected CPU history instructions or base table')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or forced-selector trace')
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    endings = [e for e in driver if e.get('type') == 'session_end']
    configs = [e for e in driver if e.get('type') == 'penalty_direction_config']
    if len(endings) != 1 or endings[0]['steps'] != 16000 or endings[0]['reason'] != 'frame_limit' or len(configs) != 1 or configs[0]['direction'] != 'Right' or configs[0]['controllers'] != 'p1':
        raise ValueError('Unexpected run configuration')
    gates = [e for e in hooks if e['site'] == 'penalty_cpu_random_gate']
    if len(gates) != 4:
        raise ValueError('Unexpected gate count')
    cases = []
    for gate in gates:
        if gate['side'] not in (0, 2) or gate['mask'] not in (3, 7, 15) or not 0 <= gate['a'] <= 7:
            raise ValueError('Unexpected native inputs')
        same = [e for e in hooks if e.get('frame') == gate['frame'] and e.get('d') == gate['d']]
        picks = [e for e in same if e['site'] == 'penalty_cpu_random_pick']
        entries = [e for e in same if e['site'] == 'penalty_cpu_history']
        writes = [e for e in same if e['site'] == 'penalty_cpu_write']
        passed = gate['a'] != 7 and (gate['a'] & 3) <= gate['level']
        if passed != (len(picks) == 1 and len(entries) == 1):
            raise ValueError('Gate outcome mismatch')
        if passed:
            pick, entry = picks[0], entries[0]
            offset = (0x1760 if gate['side'] == 0 else 0x1780) + (pick['a'] & gate['mask']) * 2
            if entry['x'] != offset or bool(writes) != (entry['a'] < 10):
                raise ValueError('History lookup mismatch')
            if writes and (len(writes) != 1 or writes[0]['a'] != entry['a'] % 5):
                raise ValueError('History direction mismatch')
        elif picks or entries or writes:
            raise ValueError('Unexpected work after rejected gate')
        cases.append({'gate': gate, 'pick': picks[0] if picks else None, 'history': entries[0] if entries else None, 'write': writes[0] if writes else None})
    return {'schema': 'issd-penalty-cpu-history/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'rom_code_offset': '0x62295', 'rom_base_table_offset': '0x63ea5', 'cases': cases,
            'limits': ['Four gates in one synthetic run; not a probability measurement.',
                       'Earlier control and difficulty branches are outside this model.',
                       'Later direction adjustment and visual mapping remain unverified.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'CPU random gates and history outcomes audited')
