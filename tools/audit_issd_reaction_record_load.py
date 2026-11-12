"""Audit roster-to-WRAM copy and the observed reaction record pointer."""
import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_catalog import EXPECTED_MD5


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(rom, assembly, jump, fall):
    data = rom.read_bytes()
    header = len(data) % 0x8000
    image = data[header:]
    if header not in (0, 512) or hashlib.md5(image).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    source_bytes, jump_bytes, fall_bytes = assembly.read_bytes(), jump.read_bytes(), fall.read_bytes()
    source = source_bytes.decode('utf8')
    def verify(start, end, tokens):
        region = source.split(start + ':', 1)[1].split(end + ':', 1)[0]
        cursor = 0
        for token in tokens:
            position = region.find(token, cursor)
            if position < 0:
                raise ValueError(f'Unexpected disassembly in {start}: {token}')
            cursor = position + len(token)
    verify('CODE_83C69A', 'CODE_83C6AE', ('LDA.w #$7E3E00', 'Player1Team', 'JSR.w CODE_83C6AE', 'Player2Team', 'JSR.w CODE_83C6AE'))
    verify('CODE_83C6C7', 'CODE_83C6E6', ('LDA.w #$0006', 'MVN $7E3E00>>16,DATA_8A8000>>16', 'ADC.w #$000A', 'ADC.w #$0007'))
    verify('CODE_83C600', 'CODE_83C639', ('STA.l $7E0008,x', 'ADC.w #$000A'))
    verify('CODE_80E8AD', 'CODE_80E8DD', ('LDX.w #$3F90', 'CMP.w #$1000', 'LDX.w #$3FA4', 'LDY.w #$00C8', 'ADC.b $68', 'AND.w #$001F', 'ADC.w DATA_8195EB,x', 'ADC.b $40', 'LDA.l $7E0000,x'))
    checks = {0x1c69a: '8b a9 00 3e 85 02', 0x1c6c7: 'a6 00 a4 02 a9 06 00 54 7e 8a',
              0x68ad: '85 40 a2 90 3f a0 00 00 7b c9 00 10 90 06 a2 a4 3f a0 c8 00'}
    for offset, value in checks.items():
        expected = bytes.fromhex(value)
        if image[offset:offset + len(expected)] != expected:
            raise ValueError(f'Unexpected ROM instructions at {offset:06X}')
    table = [int.from_bytes(image[0x95eb + 2*i:0x95ed + 2*i], 'little') for i in range(32)]
    if table[:20] != [0x3e00 + 10*i for i in range(20)]:
        raise ValueError('Unexpected player record table')
    observations = [json.loads(jump_bytes)['record'], json.loads(fall_bytes)['record']]
    resolved = []
    for record in observations:
        dp, pointer = record['d'], record['x']
        bias = 0xc8 if dp >= 0x1000 else 0
        candidates = [i for i, base in enumerate(table) if (base + bias + 2) & 0xffff == pointer]
        if candidates != [9] or dp != 0x1900 or record['target68'] != 9:
            raise ValueError('Unexpected lookup context or ambiguous index')
        resolved.append({'direct_page': dp, 'target68': record['target68'],
                         'runtime_array_address': (0x3fa4 if bias else 0x3f90) + record['target68'],
                         'inferred_low_five_bits': candidates[0], 'returned_pointer': pointer,
                         'record_base': pointer - 2, 'extra_word_address': pointer + 6})
    return {'schema': 'issd-reaction-record-load/v1', 'rom_sha256': sha(image),
            'disassembly_sha256': sha(source_bytes), 'jump_report_sha256': sha(jump_bytes),
            'fall_report_sha256': sha(fall_bytes), 'copy_routine': '83:C69A/C6AE/C6C7',
            'copy': {'source': '8A:8000', 'count_per_team': 20, 'source_stride': 7,
                     'destination_first_team': '7E:3E00', 'destination_second_team': '7E:3EC8',
                     'destination_stride': 10, 'copied_bytes_per_record': 7},
            'extra_word_write': '83:C600 writes at record offset 8 during its surrounding calculation',
            'lookup_table_rom_offset': '0x0095EB', 'observations': resolved,
            'limits': ['Static copy/lookup contract and captured return pointer; no direct observation of the runtime array byte or copy execution.',
                       'Pointer-derived index is inferred from the ROM table, not directly captured from the array.',
                       'Other routines may modify records; team identity and whole-record equality are not proven.',
                       'The generation and meaning of record offset 8, global state, and browser mappings remain unresolved.',
                       'ROM and raw traces remain local.']}


def main():
    parser = argparse.ArgumentParser()
    for name in ('rom', 'assembly', 'jump', 'fall', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.assembly, args.jump, args.fall)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: seven-byte roster copy and both observed pointers resolve to slot 9')


if __name__ == '__main__':
    main()
