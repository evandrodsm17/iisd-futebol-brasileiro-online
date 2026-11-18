"""Audit two observed penalty goalkeeper selector timelines against ROM sequences."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, hook_path):
    rom, raw = rom_path.read_bytes(), hook_path.read_bytes()
    fixtures = {0xdebb: '00 00 1c 00 1e 00 ff 0e 00 10 00 0a 00 ff',
                0x16dde: '03 03 03 00 04 0f ff 00 f4 ed ee ed',
                0x16e06: '10 ee 0a ee 30 ee 38 ee 40 ee 68 ee 48 ee'}
    for offset, text in fixtures.items():
        value = bytes.fromhex(text)
        if rom[offset:offset + len(value)] != value:
            raise ValueError(f'Unexpected ROM data at {offset:#x}')
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    writes = [e for e in hooks if e['site'] == 'penalty_selector_write']
    cases = []
    for anchor in [e for e in writes if e['value'] == 30]:
        same = [e for e in writes if e['d'] == anchor['d'] and anchor['frame'] - 3 <= e['frame'] <= anchor['frame'] + 23]
        values = [e['value'] for e in same]
        frames = [e['frame'] - same[0]['frame'] for e in same] if same else []
        if values != [28, 30, 14, 16, 10] or frames != [0, 3, 7, 11, 26]:
            raise ValueError('Unexpected selector sequence')
        for e in same:
            if not e['indexed_load'] or e['bank'] != 0x81 or e['source_byte'] != e['value'] or rom[e['source']] != e['value']:
                raise ValueError('Unexpected selector data source')
        cases.append({'side': anchor['side'], 'round': anchor['round'], 'object': anchor['d'],
                      'first_frame': same[0]['frame'], 'relative_frames': frames,
                      'selectors': values, 'source_addresses': [e['source'] for e in same],
                      'state_addresses': [e['animation_state'] for e in same]})
    if len(cases) != 2:
        raise ValueError('Expected two captured sequences')
    return {'schema': 'issd-penalty-pose-timing/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'cases': cases, 'rom_offsets_checked': [hex(offset) for offset in fixtures],
            'limits': ['Score, clock and menu commands were synthetic; selector was not forced.',
                       'Intervals describe collision-selector changes, not necessarily displayed sprite durations.',
                       'Only two occurrences and one observed action path; no general direction mapping is asserted.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'captured selector timelines audited')
