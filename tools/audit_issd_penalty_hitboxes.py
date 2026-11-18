"""Compare sampled native object collision tests with their original ROM tables."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def negative(value):
    return bool(value & 0x80)


def collision(rom, event):
    pointer = event['table_pointer']
    if not 0xde13 <= pointer < 0xde8e:
        raise ValueError('Unexpected native hitbox pointer')
    end = int.from_bytes(rom[pointer:pointer + 2], 'little')
    if not pointer + 2 < end <= 0xde8e:
        raise ValueError('Unexpected table end')
    delta_y = (event['other_y'] - event['y'] + event['offset']) & 255
    if negative(delta_y):
        delta_y = (-delta_y) & 255
    if delta_y >= 12:
        return False
    dx = (event['other_x'] - event['x']) & 255
    dz = (event['other_z'] - event['z']) & 255
    cursor = pointer + 2
    while cursor < end:
        low_x, low_z, high_x, high_z = rom[cursor:cursor + 4]
        if not negative((dz - low_z) & 255) and negative((dz - high_z - 1) & 255):
            if event['object_flags'] & 0x10:
                lower, upper = (-high_x) & 255, (-low_x) & 255
            else:
                lower, upper = low_x, high_x
            if not negative((dx - lower) & 255) and negative((dx - upper) & 255):
                return True
        cursor += 4
    return False


def audit(rom_path, hook_path):
    rom, raw = rom_path.read_bytes(), hook_path.read_bytes()
    expected = bytes.fromhex('b9 00 00 8d 00 00 c8 c8 e2 20 bd 0c 00 38 e5 0c 18 6d 0a 17 10 03 49 ff 1a c9 0c b0 40')
    if rom[0x62375:0x62375 + len(expected)] != expected:
        raise ValueError('Unexpected collision routine')
    if rom[0x63c6c:0x63c8c] != bytes.fromhex('13 de 19 de 1f de 25 de 2f de 35 de 3b de 45 de 4f de 59 de 5f de 65 de 6f de 75 de 7f de 85 de'):
        raise ValueError('Unexpected table pointers')
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete capture')
    samples = [e for e in hooks if e['site'] in ('collision_hit', 'collision_miss')]
    if not samples or not any(e['site'] == 'collision_hit' for e in samples) or not any(e['site'] == 'collision_miss' for e in samples):
        raise ValueError('Missing hit or miss observations')
    for e in samples:
        if collision(rom, e) != (e['site'] == 'collision_hit'):
            raise ValueError(f"Mismatch at frame {e['frame']}")
    counts = collections.Counter(e['site'] for e in samples)
    return {'schema': 'issd-penalty-hitboxes/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_routine_offset': '0x62375', 'rom_pointer_table_offset': '0x63c6c',
            'observed_counts': dict(counts), 'samples': samples,
            'limits': ['Negative observations are sampled; successful checks are logged individually.',
                       'Single synthetic shootout, not a full examination of all animations or hitboxes.',
                       'Byte arithmetic mirrors native wraparound; coordinates are not yet mapped to web units.',
                       'ROM and raw traces stay local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', result['observed_counts'], 'agree with native collision tests')
