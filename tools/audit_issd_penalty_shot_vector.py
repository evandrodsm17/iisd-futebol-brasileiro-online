"""Audit scene-specific penalty vector tables against a local trace."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    if rom[0x63d7c:0x63d7f] != bytes([0x28, 0, 0x50]):
        raise ValueError('Unexpected penalty table offsets')
    if rom[0x61f73:0x61f7b] != bytes.fromhex('a5 07 18 65 28 85 07 e2'):
        raise ValueError('Unexpected penalty position update')
    if rom[0x61fb9:0x61fb9 + 35] != bytes.fromhex('a5 2b 18 6d 2e 17 85 2b e2 20 a5 2d 6d 30 17 85 2d c2 20 a5 10 30 28 f0 26 64 10 a5 2b a0 02 00 22 4c 8b'):
        raise ValueError('Unexpected ground-contact routine')
    if not rom[0x62056:].startswith(bytes.fromhex('a5 2b 10 04 49 ff ff 1a c9 40 00 b0 15 a5 10 10 04 49 ff ff 1a c9 02 00 b0 08 64 2b 64 2c 64')):
        raise ValueError('Unexpected low-speed stop routine')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    ends = [e for e in driver if e.get('type') == 'session_end']
    config = [e for e in driver if e.get('type') == 'penalty_direction_config']
    if len(ends) != 1 or ends[0]['steps'] != 16000 or ends[0]['reason'] != 'frame_limit' or len(config) != 1 or config[0]['direction'] != 'Right' or config[0]['controllers'] != 'p1':
        raise ValueError('Unexpected synthetic capture')
    shots = [e for e in hooks if e['site'] == 'penalty_shot_vector']
    if not shots:
        raise ValueError('No shot vectors')
    observations = []
    for e in shots:
        variant = e['variant']
        if variant not in (0, 1, 2):
            raise ValueError('Unexpected variant')
        base = e['index'] % 5
        offset = rom[0x63d7c + variant] + 2 * base
        if e['x'] != offset:
            raise ValueError('Table index mismatch')
        address = {'dx': 0x63d95, 'dy': 0x63d8b, 'dz': 0x63da9 if e['flags'] & 0x10 else 0x63d9f}
        vectors = {}
        for name, pos in address.items():
            raw_value = int.from_bytes(rom[pos + offset:pos + offset + 2], 'little')
            if e[name] != raw_value or e[name + '_ext'] != (255 if raw_value & 0x8000 else 0):
                raise ValueError('Initial vector mismatch')
            vectors[name] = raw_value if raw_value < 0x8000 else raw_value - 0x10000
        observations.append({'frame': e['frame'], 'side': e['side'], 'variant': variant,
                             'index': e['index'], 'flags': e['flags'], 'table_offset': offset, **vectors})
    steps = [e for e in hooks if e['site'] == 'penalty_shot_step']
    comparisons = 0
    matches = 0
    bounces = []
    stopped = []
    for a, b in zip(steps, steps[1:]):
        if b['frame'] != a['frame'] + 1 or (a['side'], a['round'], a['d']) != (b['side'], b['round'], b['d']):
            continue
        if not any(a[v] for v in ('dx', 'dy', 'dz')):
            continue
        comparisons += 1
        if all(b[p] == (a[p] + a[v]) % 65536 for p, v in [('px', 'dx'), ('py', 'dy'), ('pz', 'dz')]):
            matches += 1
            continue
        if any(b[p] != (a[p] + a[v]) % 65536 for p, v in [('px', 'dx'), ('py', 'dy')]):
            raise ValueError('Unexpected horizontal displacement')
        if b['pz'] == ((a['pz'] + a['dz']) & 0xff) and b['dz'] == (-(((a['dz'] + 32) & 0xffff) // 2)) % 65536:
            bounces.append({'frame': a['frame'], 'position': a['pz'], 'velocity': a['dz'], 'next_position': b['pz'], 'next_velocity': b['dz']})
        elif b['pz'] == 0 and b['dz'] == 0:
            stopped.append({'frame': a['frame'], 'position': a['pz'], 'velocity': a['dz']})
        else:
            raise ValueError('Unclassified position change')
    if not comparisons or not matches:
        raise ValueError('No observed sequential position update')
    return {'schema': 'issd-penalty-shot-vector/v1', 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'observations': observations,
            'sequential_steps_compared': comparisons, 'sequential_steps_matching_all_low_words': matches,
            'bounce_pattern': bounces, 'stop_pattern': stopped,
            'limits': ['One synthetic shootout, not an exhaustive sample.',
                       'Low-word checks do not alone establish screen-axis orientation or full collision behaviour.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['observations']), 'initial vectors;', result['sequential_steps_matching_all_low_words'], 'matching sequential updates')
