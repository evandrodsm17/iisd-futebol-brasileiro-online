"""Audit the ROM's clock initialization and selector-9 dispatch, without assuming a match phase."""
import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_catalog import EXPECTED_MD5


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(rom, assembly):
    data = rom.read_bytes()
    header = len(data) % 0x8000
    image = data[header:]
    if header not in (0, 512) or hashlib.md5(image).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    source = assembly.read_text(encoding='utf8')
    regions = {
        'dispatch': ('CODE_A4D804:', 'DATA_A4D809:', ('ASL', 'TAX', 'JMP.w (DATA_A4D809,x)')),
        'handler': ('CODE_A4D898:', 'CODE_A4D8AA:', ('JSL.l CODE_A49231', 'INC.b $A8')),
        'clock_init': ('CODE_A49231:', 'CODE_A49243:', ('JSR.w CODE_A4926F', 'STA.w !RAM_ISSD_Global_DisplayedSecondsOnTimer', 'STA.w !RAM_ISSD_Global_GameTimerSeconds')),
        'clock_table': ('CODE_A4926F:', 'CODE_A49281:', ('LDA.w $00A8', 'LDA.w DATA_81E893,y', 'LDA.w DATA_81E89B,y')),
    }
    for name, (start, end, tokens) in regions.items():
        fragment = source.split(start, 1)[1].split(end, 1)[0]
        positions = [fragment.find(token) for token in tokens]
        if -1 in positions or positions != sorted(positions):
            raise ValueError(f'Unexpected {name} disassembly')
    checks = {
        0x125804: bytes.fromhex('0a aa 7c 09 d8'),
        0x125898: bytes.fromhex('22 07 d4 86 22 31 92 a4 22 53 92 a4 22 6d c6 83 e6 a8'),
        0x121231: bytes.fromhex('20 6f 92 8d d2 16 8d d0 16 8d e6 16'),
        0x12126f: bytes.fromhex('ad 5a 1e 0a a8 ad a8 00 d0 04 b9 93 e8 60 b9 9b e8 60'),
    }
    for offset, expected in checks.items():
        if image[offset:offset + len(expected)] != expected:
            raise ValueError(f'Unexpected opcode bytes at {offset:06x}')
    targets = [int.from_bytes(image[0x125809 + 2*i:0x12580b + 2*i], 'little') for i in range(15)]
    if targets[9] != 0xd898:
        raise ValueError('Selector 9 does not point to A4:D898')
    tables = [[int.from_bytes(image[base + 2*i:base + 2*i + 2], 'little') for i in range(4)] for base in (0xe893, 0xe89b)]
    return {'schema': 'issd-period-dispatch-static/v1', 'rom_sha256': digest(image),
            'disassembly_sha256': digest(assembly.read_bytes()),
            'dispatch': 'A4:D804', 'table': 'A4:D809', 'selector': 9,
            'target': 'A4:D898', 'clock_init': 'A4:9231',
            'clock_init_before_increment': True,
            'table_offsets': ['0x00E893', '0x00E89B'], 'table_words_bcd': tables,
            'limits': ['Static control-flow and ROM bytes only; no matching runtime observation.',
                       'INC uses direct page $A8; actual target depends on the direct-page register.',
                       'No evidence that countdown zero alone selects dispatch entry 9.',
                       'No identification of halftime, end-of-match, score transition or input handling.',
                       'The ROM is not distributed.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rom', type=Path)
    parser.add_argument('assembly', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.assembly)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: selector 9 and clock initialization match ROM and disassembly')


if __name__ == '__main__':
    main()
