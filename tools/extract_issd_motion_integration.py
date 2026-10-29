"""Preserve the native movement integration and conditional rollback evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asm', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--rom', type=Path, help='Optional local ROM for independent dimension-table verification (never copied)')
    args = parser.parse_args()
    source = args.asm.read_text(encoding='utf-8')
    body = source.split('CODE_80D2B3:', 1)[1].split('CODE_80D33F:', 1)[0]
    anchor_body = source.split('CODE_80D24D:', 1)[1].split('CODE_80D2B3:', 1)[0]
    correction_body = source.split('CODE_80E086:', 1)[1].split('CODE_80E189:', 1)[0]
    inverse_body = source.split('CODE_80E19B:', 1)[1].split('CODE_80E1AF:', 1)[0]
    dimensions_text = source.split('DATA_81EC47:', 1)[1].split('DATA_81EC67:', 1)[0]
    dimensions = [int(word, 16) for word in re.findall(r'\$([0-9A-F]{4})', dimensions_text)]
    if len(dimensions) != 16:
        raise ValueError('expected eight native dimension pairs')
    rom_verification = {'status': 'not_checked'}
    if args.rom:
        rom_bytes = args.rom.read_bytes()
        header_size = 512 if len(rom_bytes) % 32768 == 512 else 0
        if len(rom_bytes) % 32768 not in (0, 512):
            raise ValueError('unsupported ROM size/header layout')
        # LoROM $81:EC47 => unheadered file offset $00EC47.
        offset = 0xEC47 + header_size
        expected_bytes = b''.join(value.to_bytes(2, 'little') for value in dimensions)
        if rom_bytes[offset:offset + 32] != expected_bytes:
            raise ValueError('ROM dimension table differs from disassembly at $81:EC47')
        rom_verification = {'status': 'byte_exact', 'snes_address': '$81:EC47', 'unheadered_file_offset': '$00EC47', 'copier_header_bytes': header_size, 'length': 32, 'rom_sha256': hashlib.sha256(rom_bytes).hexdigest()}
    initializer = source.split('CODE_A4E0B3:', 1)[1].split('STA.w $12E2', 1)[0] + 'STA.w $12E2'
    expected = ['LDA.w $0086', 'ASL', 'ASL', 'TAY', 'LDA.w DATA_81EC67+$02,y', 'STA.w $12D0', 'LDA.w DATA_81EC47,y', 'STA.w $12A2', 'LSR', 'STA.w $12F2', 'LDA.w DATA_81EC47+$02,y', 'STA.w $12A4', 'LSR', 'STA.w $12D8']
    if '\n'.join(expected) not in '\n'.join(line.strip() for line in initializer.splitlines()):
        raise ValueError('dimension initializer prefix changed')
    normalized_initializer = '\n'.join(line.strip() for line in initializer.splitlines())
    formulas = [
        ['LDA.w $12D8', 'CLC', 'ADC.w #$0030', 'STA.w $12E6', 'SEC', 'SBC.w #$0060', 'STA.w $12E4'],
        ['LDA.w $12A4', 'CLC', 'ADC.w #$0018', 'STA.w $12E0'],
        ['LDA.w #$FFC8', 'STA.w $12E8'],
        ['LDA.w $12A2', 'CLC', 'ADC.w #$0038', 'STA.w $12EA', 'CLC', 'ADC.w #$0048', 'STA.w $12E2'],
    ]
    for sequence in formulas:
        if '\n'.join(sequence) not in normalized_initializer:
            raise ValueError('dimension limit formula changed: ' + sequence[-1])
    stadium_transfer = ['LDA.w !RAM_ISSD_MainMenu_SelectedStadium', 'AND.w #$0007', 'STA.w $0086', 'STA.w !RAM_ISSD_MainMenu_SelectedStadium']
    if '\n'.join(stadium_transfer) not in '\n'.join(line.strip() for line in source.splitlines()):
        raise ValueError('selected stadium transfer changed')
    dimension_cases = []
    for index in range(8):
        width, height = dimensions[index * 2:index * 2 + 2]
        dimension_cases.append({'selector': index, '$12A2': width, '$12A4': height, '$12D8': height >> 1,
                                '$12E0': height + 24, '$12E2': width + 128,
                                '$12E4': (height >> 1) - 48, '$12E6': (height >> 1) + 48,
                                '$12E8': 0xFFC8, '$12EA': width + 56})
    for instruction in ('CPY.w #$FFE8', 'CPX.w #$FF80', 'CPX.w $12A2', 'CODE_80E164:', 'JSL.l CODE_80E19B', 'STX.b $08', 'STY.b $0C'):
        if instruction not in correction_body:
            raise ValueError(f'changed coordinate correction: {instruction}')
    for instruction in ('LDX.w #$7ED724', 'LDX.w #$7ED750', 'CMP.w #$1000', 'TSB.b $6C', 'SBC.w #$0060', 'CODE_80D298:'):
        if instruction not in anchor_body:
            raise ValueError(f'changed anchor constraint: {instruction}')
    for low, high, delta_low, delta_high in [('06', '08', '22', '24'), ('0A', '0C', '26', '28')]:
        for flag, operation in [('CLC', 'ADC'), ('SEC', 'SBC')]:
            sequence = [f'LDA.b ${low}', flag, f'{operation}.b ${delta_low}', f'STA.b ${low}', f'LDA.b ${high}', f'{operation}.b ${delta_high}', f'STA.b ${high}']
            normalized = '\n'.join(line.strip() for line in body.splitlines())
            if '\n'.join(sequence) not in normalized:
                raise ValueError(f'changed native {operation} chain for ${low}/${high}')
    payload = {
        'schema_version': 1,
        'source': {'assembly': str(args.asm), 'entry': 'CODE_80:D2B3', 'end_exclusive': 'CODE_80:D33F', 'body_sha256': hashlib.sha256(body.encode()).hexdigest()},
        'integration': ['[$08:$06] += [$24:$22]', '[$0C:$0A] += [$28:$26]'],
        'rollback_gates': ['$12F6 bit $0004 set', 'local $6C bit $2000 clear', 'direct page differs from $11E8', 'both native range tests finish with carry clear'],
        'range_tests': [{'axis': '$08', 'target': '$0408', 'bias': '$0070', 'limit': '$00E0'}, {'axis': '$0C', 'target': '$040C', 'bias': '$0050', 'limit': '$00A0'}],
        'carry_rule': 'CLC; ADC position; SBC target; SEC; SBC limit. The first SBC inherits carry from ADC.',
        'rollback': 'subtract the same two 32-bit deltas, including low-word borrow',
        'derived_coordinates': {'$2C': '$009A + $0C modulo 65536', '$2A': '$0098 + $08 - $2C modulo 65536'},
        'tail': ['call CODE_80:E086 only if $00D0 is zero', 'jump CODE_80:D24D if $12FA is negative; otherwise RTL'],
        'assembly_excerpt': body.strip(),
        'limit_provenance': {
            'entry': 'CODE_A4:E0B3', 'table': 'DATA_81:EC47',
            'rom_verification': rom_verification,
            'selector': 'global $0086 shifted left twice selects a pair of words',
            'menu_provenance': 'CODE_85:A4F8 transfers MainMenu_SelectedStadium & $0007 to $0086 and back to MainMenu_SelectedStadium',
            'scope': '$0086 also receives 8, 9 and 10 in other scene-loading routes; the eight-row dimension table is not its global domain',
            'cases': dimension_cases, 'assembly_excerpt': initializer.strip(),
            'limitation': 'Numeric selectors are not assigned stadium names; only the eight table records are enumerated.',
        },
        'coordinate_correction': {
            'entry': 'CODE_80:E086',
            'outer_limits': {'$2C': ['$FFE8', '$12E0'], '$2A': ['$FF80', '$12E2']},
            'comparison_semantics': 'outer bounds use N from CPY/CPX via BMI/BPL, not a general signed comparison with overflow correction',
            'inner_gate': 'after outer X bounds, CPX $12A2; carry clear skips the inner corrections',
            'inner_reference_words': ['$12E4', '$12E6', '$12E8', '$12EA'],
            'inner_candidates': 'Y references use thresholds $0006/$FFFA and offsets +7/-7; X references use $000C/$FFF4 and offsets +13/-13, preserving flags from each CMP',
            'candidate_selection': 'restore Y from $2C if $42 is neither 0 nor 2; restore X from $2A if $40 is nonzero; store X/Y into $2A/$2C',
            'inverse_gate': 'E179 returns only when both Y and X are zero; otherwise calls E19B and writes X/Y to $08/$0C',
            'inverse': {'Y': 'input Y - global $009A modulo 65536', 'X': 'input X + input Y - global $0098 modulo 65536', 'scratch': 'input Y is stored in absolute $0000'},
            'fractional_words': '$06/$0A are not written by E086..E188 or E19B',
            'assembly_excerpt': correction_body.strip(),
            'inverse_assembly_excerpt': inverse_body.strip(),
        },
        'anchor_constraint': {
            'entry': 'CODE_80:D24D',
            'base_selection': '$7E:D724 for direct page below $1000, otherwise $7E:D750',
            'index': 'local $68 shifted left twice, then ADC base; carry from the second ASL is preserved',
            'initialization': 'if local $6C bit $0800 is clear, set it and store local $2A/$2C in the selected four-byte record',
            'tests': 'for each derived coordinate: LDA #$0030; CLC; ADC coordinate; SBC saved coordinate; SEC; SBC #$0060',
            'rejection': 'carry set after either test enters CODE_80:D298 and subtracts both 32-bit movement deltas',
            'derived_coordinate_refresh': 'D298 does not recompute local $2A/$2C after subtraction',
            'assembly_excerpt': anchor_body.strip(),
        },
        'limitations': ['The range predicate retains native carry semantics; it is not simplified to a geometric rectangle.', 'Meanings of flags, tail helpers and browser-unit conversion remain unresolved.', 'No browser physics change is authorized by this artifact alone.'],
    }
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
