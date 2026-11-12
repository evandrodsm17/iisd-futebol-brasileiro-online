"""Audit the static three-bit extraction used for runtime player record +8."""
import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_catalog import EXPECTED_MD5


def audit(rom, assembly):
    data = rom.read_bytes()
    header = len(data) % 0x8000
    image = data[header:]
    if header not in (0, 512) or hashlib.md5(image).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    asm_bytes = assembly.read_bytes()
    text = asm_bytes.decode('utf8')
    region = text.split('CODE_83C5EC:', 1)[1].split('CODE_83C639:', 1)[0]
    cursor = 0
    for token in ('LDY.w #$0005', 'CODE_83C600:', 'LDA.b $08', 'AND.w #$0007', 'STA.l $7E0008,x',
                  'LSR.b $08', 'LSR.b $08', 'LSR.b $08', 'ADC.w #$000A', 'DEY', 'BNE.b CODE_83C600'):
        pos = region.find(token, cursor)
        if pos < 0:
            raise ValueError(f'Missing or reordered instruction: {token}')
        cursor = pos + len(token)
    expected = bytes.fromhex('a5 08 29 07 00 9f 08 00 7e 46 08 46 08 46 08 8a 18 69 0a 00 aa 88 d0 e8')
    if image[0x1c600:0x1c600 + len(expected)] != expected:
        raise ValueError('Unexpected ROM bytes at 83:C600')
    table = [int.from_bytes(image[0xae8f + 2*i:0xae91 + 2*i], 'little') for i in range(16)]
    return {'schema': 'issd-reaction-extra-field-static/v1', 'rom_sha256': hashlib.sha256(image).hexdigest(),
            'disassembly_sha256': hashlib.sha256(asm_bytes).hexdigest(), 'routine': '83:C5EC/C600',
            'lookup_table': '81:AE8F', 'table_words': table, 'group_size': 5, 'bits_per_value': 3,
            'destination_record_stride': 10, 'destination_offset': 8,
            'limits': ['Static code and bytes; the input work word is not observed for the replay.',
                       'The preceding rotation and lookup depend on runtime state and direct-page context.',
                       'A later special-case write may alter a record; this does not model the complete initialization.',
                       'The value at +8 can be modified by other routines; no gameplay or attribute meaning is established.',
                       'The attempted isolated replay did not produce a capture; ROM and state remain local.']}


def main():
    parser = argparse.ArgumentParser()
    for name in ('rom', 'assembly', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.assembly)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: ROM and disassembly agree on five three-bit fields')


if __name__ == '__main__':
    main()
