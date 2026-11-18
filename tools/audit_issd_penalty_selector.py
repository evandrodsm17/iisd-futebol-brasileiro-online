"""Audit native collision table selection without assigning animation names."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def audit(rom_path, hooks_path):
    rom, raw = rom_path.read_bytes(), hooks_path.read_bytes()
    code = bytes.fromhex('a5 36 5b a6 14 bf 6c bc 8c a8 a6 1a 20 75 a3')
    if rom[0x614cf:0x614cf + len(code)] != code:
        raise ValueError('Unexpected selector instructions')
    pointers = [int.from_bytes(rom[0x63c6c + i * 2:0x63c6e + i * 2], 'little') for i in range(16)]
    if pointers != [0xde13, 0xde19, 0xde1f, 0xde25, 0xde2f, 0xde35, 0xde3b, 0xde45,
                    0xde4f, 0xde59, 0xde5f, 0xde65, 0xde6f, 0xde75, 0xde7f, 0xde85]:
        raise ValueError('Unexpected pointer table')
    tables = []
    for i, pointer in enumerate(pointers):
        end = int.from_bytes(rom[pointer:pointer + 2], 'little')
        if end <= pointer + 2 or end > 0xde8e:
            raise ValueError('Unexpected table end')
        tables.append({'selector': i * 2, 'pointer': pointer, 'end': end, 'payload_bytes': end - pointer - 2,
                       'payload_divisible_by_four': (end - pointer - 2) % 4 == 0})
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete trace')
    samples = [e for e in hooks if e['site'] in ('collision_hit', 'collision_miss')]
    if not samples or not any(e['site'] == 'collision_hit' for e in samples):
        raise ValueError('No sampled contacts')
    for event in samples:
        selector = event['selector']
        if selector % 2 or not 0 <= selector < 32 or pointers[selector // 2] != event['table_pointer']:
            raise ValueError(f"Selector mismatch at frame {event['frame']}")
    counts = collections.Counter(f"{e['selector']:02x}" for e in samples)
    return {'schema': 'issd-penalty-selector/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_selector_offset': '0x614cf', 'rom_pointer_table_offset': '0x63c6c', 'tables': tables,
            'sample_counts_by_selector': dict(counts), 'samples': samples,
            'limits': ['Negative collision observations are sampled; positive checks are recorded individually.',
                       'The selector has not been associated with named goalkeeper animations.',
                       'The final table has seven payload bytes and needs separate interpretation.',
                       'One synthetic shootout; ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['samples']), 'selector observations and', len(result['tables']), 'ROM entries')
