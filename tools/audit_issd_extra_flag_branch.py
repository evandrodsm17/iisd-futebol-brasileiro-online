"""Audit a synthetic replay of the alternate roster-state flag branch."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def audit(control_path, flag_path, rom_path):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Unexpected ROM')
    code = bytes.fromhex('a9 04 00 80 03 a9 02 00 e2 20 a0 28 00 a2 00 3e 9f 08 00 7e 88 d0 f9 c2 20 6b')
    if rom[0x1c579:0x1c593] != code:
        raise ValueError('Unexpected alternate-branch opcodes')
    control_raw, flag_raw = control_path.read_bytes(), flag_path.read_bytes()
    control = [json.loads(line) for line in control_raw.splitlines()]
    events = [json.loads(line) for line in flag_raw.splitlines()]
    if any(e.get('site') == 'error' for e in events):
        raise ValueError('Probe failed')
    markers = [e for e in events if e['site'] == 'flag_intervention']
    restores = [e for e in events if e['site'] == 'flag_restore']
    if len(markers) != 1 or len(restores) != 1 or markers[0]['original'] != 0 or markers[0]['replacement'] != 0x100 or restores[0]['value'] != 0:
        raise ValueError('Unexpected intervention or restore')
    entries = [e for e in events if e['site'] == 'entry']
    reference_entries = [e for e in control if e['site'] == 'entry']
    if len(entries) != 5 or len(reference_entries) != 5 or any(entries[i]['seed'] != reference_entries[i]['seed'] for i in range(5)):
        raise ValueError('Generator input changed')
    if entries[-1]['flags'] & 0x100 == 0 or entries[-1]['frame'] != 1948:
        raise ValueError('Flag not active at the fifth entry')
    prior = [e for e in events if e['site'] == 'stored']
    control_prior = [e for e in control if e['site'] == 'stored' and e['frame'] < 1948]
    fields = ('frame', 'x', 'record_extra')
    if len(prior) != 160 or len(control_prior) != 160 or any(any(a[k] != b[k] for k in fields) for a, b in zip(prior, control_prior)):
        raise ValueError('First four generations differed')
    before = [e for e in events if e['site'] == 'override_assign']
    after = [e for e in events if e['site'] == 'override_stored']
    if len(before) != 40 or len(after) != 40:
        raise ValueError('Expected 40 branch stores')
    for b, a in zip(before, after):
        if b['x'] != 0x3e00 or a['x'] != 0x3e00 or b['a'] & 255 != 4 or a['record_extra'] & 255 != 4:
            raise ValueError('Unexpected branch write')
    previous = {e['x']: e['record_extra'] for e in prior if e['frame'] == 1800}
    initialized = [e for e in events if e['site'] == 'actor_init']
    if len(previous) != 40 or len(initialized) != 22:
        raise ValueError('Missing previous records or actor initialization')
    for e in initialized:
        expected = (previous[e['x']] & 0xff00) | 4 if e['x'] == 0x3e00 else previous[e['x']]
        if e['record_extra'] != expected:
            raise ValueError('Observed actor value differs from prior store')
    return {'schema': 'issd-roster-extra-flag-branch/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'control_trace_sha256': hashlib.sha256(control_raw).hexdigest(),
            'intervention_trace_sha256': hashlib.sha256(flag_raw).hexdigest(),
            'injected_flag': '0x0100', 'injection_frame': 1948, 'restored_flag_word': 0,
            'prior_stores_matching_control': len(prior), 'branch_store_count': len(after),
            'branch_record_address': '0x3E00', 'branch_written_low_byte': 4,
            'actor_initializations_checked': len(initialized),
            'actor_values_matching_previous_except_target': 21,
            'initialized_extra_distribution': dict(sorted(collections.Counter(e['record_extra'] for e in initialized).items())),
            'limits': ['Bit 0x0100 was artificially set in emulator RAM immediately before a single call and restored on return.',
                       'This confirms only this entry path in the USA ROM; CODE_83C57E and natural flag-setting contexts are not tested.',
                       'The meaning and intended use of the branch remain unknown; no bug or designer intent is inferred.',
                       'Observed values do not exclude uninstrumented writes.',
                       'ROM and raw traces are not distributed.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ('control', 'flag', 'rom', 'output'):
        p.add_argument(key, type=Path)
    a = p.parse_args()
    report = audit(a.control, a.flag, a.rom)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: 40 stores to the same record; 22 initialized records checked')
