"""Compare disposable startup replays with controlled generator inputs."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from audit_issd_extra_state import generate


def read(path):
    raw = path.read_bytes()
    return raw, [json.loads(line) for line in raw.splitlines()]


def audit(baseline_path, zero_path, max_path, rom_path):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Unexpected ROM')
    table = [int.from_bytes(rom[0xae8f+2*i:0xae91+2*i], 'little') for i in range(16)]
    runs = [read(p) for p in (baseline_path, zero_path, max_path)]
    normalized = []
    for (raw, events), value in zip(runs, (None, 0, 65535)):
        entries = [r for r in events if r['site'] == 'entry']
        changes = [r for r in events if r['site'] == 'intervention']
        restores = [r for r in events if r['site'] == 'restore']
        if len(entries) != 5 or (value is None and (changes or restores)):
            raise ValueError('Unexpected startup or baseline intervention')
        if value is not None and (len(changes) != 1 or len(restores) != 1 or changes[0]['replacement'] != value or changes[0]['original'] != 56981 or restores[0]['value'] != 56981):
            raise ValueError('Unexpected intervention or restore')
        expected_seed = 56981 if value is None else value
        if entries[-1]['seed'] != expected_seed or entries[-1]['frame'] != 1948:
            raise ValueError('Unexpected generator input')
        start = events.index(entries[-1])
        final = events[start:]
        teams = [r for r in final if r['site'] == 'team']
        assigns = [r for r in final if r['site'] == 'assign']
        stored = [r for r in final if r['site'] == 'stored']
        initial = [r for r in final if r['site'] == 'actor_init']
        if len(teams) != 2 or len(assigns) != 40 or len(stored) != 40 or len(initial) != 22:
            raise ValueError('Incomplete records')
        expected = generate(expected_seed, (-expected_seed)&0xffff, table) + generate((-expected_seed)&0xffff, expected_seed, table)
        if [(r['bits'] & 7) for r in assigns] != expected or [r['record_extra'] for r in stored] != expected:
            raise ValueError('Seed did not produce expected values')
        if any(a['x'] != b['x'] for a, b in zip(assigns, stored)):
            raise ValueError('Mismatched store address')
        init = {r['x']: r['record_extra'] for r in initial}
        if len(init) != 22:
            raise ValueError('Duplicated initialized record')
        normalized.append({'sha256': hashlib.sha256(raw).hexdigest(), 'seed': expected_seed,
                           'prior_seeds': [r['seed'] for r in entries[:-1]], 'initial': init})
    if len({tuple(r['prior_seeds']) for r in normalized}) != 1:
        raise ValueError('Early generator inputs differ')
    baseline = normalized[0]['initial']
    summaries = []
    for row in normalized:
        if set(row['initial']) != set(baseline):
            raise ValueError('Initialized roster identity changed')
        summaries.append({'seed': row['seed'], 'trace_sha256': row['sha256'],
                          'changed_initialized_records': sum(row['initial'][k] != baseline[k] for k in baseline),
                          'extra_distribution': dict(sorted(collections.Counter(row['initial'].values()).items()))})
    return {'schema': 'issd-roster-extra-seed-intervention/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'prior_generator_inputs': normalized[0]['prior_seeds'], 'cases': summaries,
            'limits': ['Inputs 0 and 65535 were injected into emulator RAM at the fifth generator entry and original value restored after both teams.',
                       'Comparison covers generator hooks and initialized record values, not all machine state.',
                       'One automated startup and one intervention point; no claim about natural probability or gameplay semantics.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('baseline', 'zero', 'maximum', 'rom', 'output'):
        parser.add_argument(key, type=Path)
    a = parser.parse_args()
    report = audit(a.baseline, a.zero, a.maximum, a.rom)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: paired seeds, 120 generated outputs and 22 initialized records per case')
