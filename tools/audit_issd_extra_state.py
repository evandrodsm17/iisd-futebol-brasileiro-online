"""Audit the roster extra-state generator against ROM bytes and hook observations."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def generate(source, shift, table):
    result = []
    for _ in range(4):
        rotations = (shift >> 12) + 1
        shift = (shift << 4) & 0xffff
        bits = table[source & 15]
        source >>= 4
        for _ in range(rotations):
            bits = (bits >> 3) | ((bits & 7) << 12)
        for _ in range(5):
            result.append(bits & 7)
            bits >>= 3
    return result


def audit(trace_path, rom_path):
    raw, rom = trace_path.read_bytes(), rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Expected headerless USA ROM')
    if rom[0x1c600:0x1c609] != bytes.fromhex('a5 08 29 07 00 9f 08 00 7e'):
        raise ValueError('Unexpected store opcodes')
    generator = bytes.fromhex('7b 06 02 2a 06 02 2a 06 02 2a 06 02 2a 1a 85 06 a5 00 46 00 46 00 46 00 46 00 29 0f 00 0a a8 b9 8f ae 85 08 7b 46 08 6a 46 08 6a 46 08 6a 4a 04 08 c6 06 d0 ef a0 05 00')
    if rom[0x1c5c8:0x1c600] != generator:
        raise ValueError('Unexpected generator opcodes')
    table = [int.from_bytes(rom[0xae8f+i*2:0xae91+i*2], 'little') for i in range(16)]
    if any(value > 0x7fff for value in table):
        raise ValueError('Rotation table exceeds 15 bits')
    events = [json.loads(line) for line in raw.splitlines()]
    pending, team, seed, matched, calls, initializations = None, None, None, 0, [], []
    last_store = {}
    for event in events:
        site = event['site']
        if site == 'entry':
            if event['d'] != 0 or event['flags'] & 0x100:
                raise ValueError('Unexpected entry or override')
            seed = event['seed']
            calls.append({'frame': event['frame'], 'seed': seed, 'teams': []})
        elif site == 'team':
            if seed is None or event['d'] != 0 or event['x'] not in (0x3e00, 0x3ec8):
                raise ValueError('Unexpected team setup')
            expected = (seed, (-seed) & 0xffff) if event['x'] == 0x3e00 else ((-seed) & 0xffff, seed)
            if (event['source'], event['shift']) != expected:
                raise ValueError('Unexpected seed transformation')
            team = {'base': event['x'], 'expected': generate(*expected, table), 'assignments': []}
            calls[-1]['teams'].append(team)
        elif site == 'assign':
            if pending or team is None:
                raise ValueError('Unexpected assignment')
            index = len(team['assignments'])
            if index >= 20 or event['x'] != team['base'] + 10 * index or (event['bits'] & 7) != team['expected'][index]:
                raise ValueError('Generator differs from instruction snapshot')
            pending = event
        elif site == 'stored':
            if not pending or pending['x'] != event['x'] or event['record_extra'] != (pending['bits'] & 7):
                raise ValueError('Store differs from assigned value')
            team['assignments'].append(event['record_extra'])
            last_store[event['x']] = event['record_extra']
            pending = None
            matched += 1
        elif site == 'actor_init':
            initializations.append({'actor': event['d'], 'record': event['x'], 'extra': event['record_extra'],
                                    'last_observed_store': last_store.get(event['x'])})
        elif site == 'end':
            if pending or team is None or len(team['assignments']) != 20:
                raise ValueError('Incomplete team generation')
            team = None
        else:
            raise ValueError('Unexpected or failed probe')
    if pending or len(calls) != 5 or matched != 200 or len(initializations) != 22:
        raise ValueError('Insufficient observations')
    if any(len(call['teams']) != 2 for call in calls):
        raise ValueError('Missing team')
    matches = sum(x['extra'] == x['last_observed_store'] for x in initializations)
    if matches != 22:
        raise ValueError('Generated value differs at actor initialization')
    return {'schema': 'issd-roster-extra-state/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'trace_sha256': hashlib.sha256(raw).hexdigest(), 'table_address': '81:AE8F',
            'generator': '83:C593..C639', 'observed_entries': len(calls),
            'observed_stores': matched, 'actor_initializations_matched_to_last_store': matches,
            'inputs': [{'frame': c['frame'], 'seed': c['seed']} for c in calls],
            'initialization_extra_distribution': dict(sorted(collections.Counter(x['extra'] for x in initializations).items())),
            'limits': ['One automated startup; no proof of the semantic meaning of seed or generated state.',
                       'Observed path has flag $0100 clear; alternative branch was not exercised.',
                       'Matching values across hooks does not prove no intermediate writes occurred.',
                       'Special post-generation correction is not independently modeled.',
                       'ROM and raw trace are not distributed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('trace', 'rom', 'output'):
        parser.add_argument(name, type=Path)
    a = parser.parse_args()
    report = audit(a.trace, a.rom)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {report['observed_stores']} stores, {report['actor_initializations_matched_to_last_store']} initializations")
