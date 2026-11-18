"""Audit native penalty direction decoding, before the later CPU adjustment."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    code = bytes.fromhex('e2 20 a2 04 00 ad 1b 14 29 0b dd d8 dd f0 06 ca 10 f3 a2 02 00 c2 20 8a 60')
    table = bytes([1, 9, 8, 10, 2])
    # Table is $81:DDD8; file offset is $DDD8 in unheadered LoROM.
    if rom[0x61e2b:0x61e2b + len(code)] != code or rom[0xddd8:0xdddd] != table:
        raise ValueError('Unexpected native decoder')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    events = [e for e in hooks if e['site'] in ('penalty_direction_decode_start', 'penalty_direction_decode_end')]
    if len(events) < 2 or len(events) % 2:
        raise ValueError('Missing paired decoder events')
    cases = []
    for start, end in zip(events[::2], events[1::2]):
        if start['site'] != 'penalty_direction_decode_start' or end['site'] != 'penalty_direction_decode_end' or start['frame'] != end['frame'] or start['input_word'] != end['input_word']:
            raise ValueError('Decoder event mismatch')
        code_value = (start['input_word'] >> 8) & 0x0b
        expected = list(table).index(code_value) if code_value in table else 2
        if end['a'] != expected:
            raise ValueError('Unexpected decoder result')
        cases.append({'frame': start['frame'], 'side': start['side'], 'round': start['round'],
                      'input_word': start['input_word'], 'code': code_value, 'base_result': end['a']})
    return {'schema': 'issd-penalty-direction-decode/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_code_offset': '0x61e2b', 'rom_table_offset': '0xddd8', 'table': list(table), 'cases': cases,
            'limits': ['One synthetic shootout with input held on controller 1.',
                       'This captures the base result before 8C:A249 can replace it and before later adjustments.',
                       'Input bits have not been mapped universally to button roles or visual directions.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'native direction decoder calls audited')
