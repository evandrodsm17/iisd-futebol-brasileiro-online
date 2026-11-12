"""Inventory direct callers of the native roster accessor, without inferring gameplay."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def audit(rom_path, asm_path):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Expected headerless USA ROM')
    source = asm_path.read_text(encoding='utf8')
    routine = source.split('CODE_80E8AD:', 1)[1].split('CODE_80E8DD:', 1)[0]
    for token in ('STA.b $40', 'ADC.b $68', 'AND.w #$001F', 'ADC.w DATA_8195EB,x', 'ADC.b $40', 'LDA.l $7E0000,x'):
        if token not in routine:
            raise ValueError('Unexpected accessor: ' + token)
    if rom[0x68ad:0x68b3] != bytes.fromhex('85 40 a2 90 3f a0'):
        raise ValueError('Unexpected accessor opcode')
    lines = source.splitlines()
    label = None
    calls = []
    for i, line in enumerate(lines):
        match = re.fullmatch(r'(CODE_[0-9A-F]{6}):', line.strip())
        if match:
            label = match.group(1)
        if line.strip() == 'JSL.l CODE_80E8AD':
            previous = lines[i - 1].strip()
            immediate = re.fullmatch(r'LDA.w #\$([0-9A-F]{4})', previous)
            calls.append({'containing_label': label, 'source_line': i + 1,
                          'immediate_offset': int(immediate.group(1), 16) if immediate else None})
    if not calls or any(call['immediate_offset'] is None for call in calls):
        raise ValueError('Accessor calls require manual review')
    # The nearby 83:D155 route uses a *different* table: byte 7 of each record.
    table = list(rom[0xb069:0xb069 + 20])
    if table != [7 + 10 * i for i in range(20)]:
        raise ValueError('Unexpected 81:B069 table')
    offsets = sorted({call['immediate_offset'] for call in calls})
    if offsets != [1, 2, 3, 4, 8]:
        raise ValueError('Accessor call set changed; review findings')
    return {'schema': 'issd-attribute-consumers/v1',
            'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'assembly_sha256': hashlib.sha256(source.encode('utf8')).hexdigest(),
            'accessor': '80:E8AD', 'call_count': len(calls), 'immediate_offsets': offsets,
            'calls': calls, 'separate_table': {'address': '81:B069', 'values': table,
            'used_by': '83:D155', 'record_offset': 7},
            'limits': ['Inventory covers textual direct JSL calls only, not indirect accesses or other accessors.',
                       'Static analysis does not establish the gameplay meaning of any call.',
                       'Offsets 7 and 8 are beyond the seven cartridge bytes; runtime state may change.',
                       'ROM and emulator traces are not distributed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('rom', 'assembly', 'output'):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.assembly)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {report['call_count']} chamadas diretas; offsets {report['immediate_offsets']}")
