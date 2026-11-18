"""Audit observed deferred penalty resolution without inferring its cause."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, hooks_path):
    rom, raw = rom_path.read_bytes(), hooks_path.read_bytes()
    expected = bytes.fromhex('22 5e 84 85 20 a7 9f 20 56 a0 a5 08 05 0c 89 00 ff f0 10 c6 24 10 0c ad aa 14 29 ff f7 8d aa 14 4c c1 8d a5 28 05 29 05 32 05 33 05 10 f0 e8 6b')
    if rom[0x60e58:0x60e58 + len(expected)] != expected:
        raise ValueError('Unexpected deferred-resolution instructions')
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete capture')
    starts = [e for e in hooks if e['site'] == 'penalty_deferred_start']
    finals = [(i, e) for i, e in enumerate(hooks) if e['site'] == 'penalty_deferred_finalize']
    if len(starts) != 3 or len(finals) != 3:
        raise ValueError('Unexpected deferred route count')
    results = []
    for index, event in finals:
        matching = [s for s in starts if s['d'] == event['d'] and s['side'] == event['side'] and s['round'] == event['round'] and s['frame'] < event['frame']]
        if len(matching) != 1 or not event['shot_flags'] & 0x0800:
            raise ValueError('Deferred start or flag missing')
        zero = all(event[k] == 0 for k in ('field_28', 'field_29', 'field_32', 'field_33', 'height'))
        if not zero:
            raise ValueError('Observed finalization was not the all-zero path')
        following = hooks[index + 1] if index + 1 < len(hooks) else {}
        if following.get('site') != 'penalty_crossing_resolved' or following.get('frame') != event['frame'] or following.get('d') != event['d']:
            raise ValueError('Missing matching resolution')
        if following['shot_flags'] & 0x0800 or (following['penalty_home'], following['penalty_away']) != (event['penalty_home'], event['penalty_away']):
            raise ValueError('Unexpected flag or score after resolution')
        results.append({'start': matching[0], 'finalize': event, 'resolved': following})
    return {'schema': 'issd-penalty-deferred/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_offset': '0x60e58', 'cases': results,
            'limits': ['One synthetic shootout; no cause such as goalkeeper save has been established.',
                       'Only the all-zero finalization path was observed; timer path is a static translation.',
                       'The three update routines before the tested conditions are not modelled.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'deferred resolutions audited')
