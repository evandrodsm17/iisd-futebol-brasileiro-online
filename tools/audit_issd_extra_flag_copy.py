"""Audit source-word copying into the roster-state mode flag."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(control_path, patched_path, rom_path):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Unexpected ROM')
    code = bytes.fromhex('8b a9 5f 00 a2 ff dd a0 40 16 54 00 7e ab af 44 d4 7e 8d aa 14 6b 8b a9 5f 00 a2 40 16 a0 ff dd 54 7e 00 ab ad aa 14 8f 44 d4 7e 6b')
    if rom[0x2b931:0x2b95d] != code:
        raise ValueError('Unexpected bidirectional copy opcodes')
    raw_control, raw_patch = control_path.read_bytes(), patched_path.read_bytes()
    control = [json.loads(line) for line in raw_control.splitlines()]
    patch = [json.loads(line) for line in raw_patch.splitlines()]
    def site(rows, name): return [r for r in rows if r['site'] == name]
    if site(patch, 'error') or len(site(control, 'copy_start')) != 2 or len(site(patch, 'copy_start')) != 2:
        raise ValueError('Incomplete copy observations')
    pre, post = site(patch, 'copy_start')[1], site(patch, 'copy_end')[1]
    control_pre, control_post = site(control, 'copy_start')[1], site(control, 'copy_end')[1]
    intervention, restore = site(patch, 'source_intervention'), site(patch, 'source_restore')
    if len(intervention) != 1 or len(restore) != 1 or intervention[0]['original'] != 0 or intervention[0]['replacement'] != 0x100:
        raise ValueError('Unexpected intervention')
    if any(r['frame'] != 2324 for r in (pre, post, control_pre, control_post, intervention[0], restore[0])):
        raise ValueError('Replay timing changed')
    if (control_pre['source_flags'], control_post['flags']) != (0, 0) or (pre['source_flags'], post['flags']) != (0x100, 0x100):
        raise ValueError('Source/destination do not match')
    if (restore[0]['source'], restore[0]['destination']) != (0, 0):
        raise ValueError('Intervention was not restored')
    copied = [r for r in patch[patch.index(pre):patch.index(post)] if r['site'] == 'flag_write']
    if [(r['pc'], r['x'], r['y']) for r in copied] != [(0x85b954, 0x1648, 0xde07), (0x85b954, 0x1649, 0xde08)]:
        raise ValueError('Unexpected observed byte-copy sequence')
    control_init, patch_init = site(control, 'actor_init'), site(patch, 'actor_init')
    if len(control_init) != 22 or control_init != patch_init:
        raise ValueError('Subsequent sampled player initializations differ')
    return {'schema': 'issd-roster-extra-flag-copy/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'control_trace_sha256': hashlib.sha256(raw_control).hexdigest(),
            'intervention_trace_sha256': hashlib.sha256(raw_patch).hexdigest(),
            'copy_routine': '85:B947', 'source_word': '7E:1648', 'destination_word': '7E:DE07',
            'byte_copy_pc': '85:B954', 'frame': 2324, 'control_value': 0, 'synthetic_value': 256,
            'copy_byte_addresses': [['7E:1648', '7E:DE07'], ['7E:1649', '7E:DE08']],
            'subsequent_actor_initializations_matching': 22,
            'limits': ['Source bit was altered artificially in emulator RAM for one copy and restored with destination.',
                       'The natural mode or user option represented by bit 0x0100 remains unknown.',
                       'The control startup did not naturally invoke the flag-on generator branch.',
                       'Comparison covers sampled fields, not the entire machine state.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ('control', 'patched', 'rom', 'output'):
        p.add_argument(key, type=Path)
    a = p.parse_args()
    report = audit(a.control, a.patched, a.rom)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: source bit copied in isolated replay and restored')
