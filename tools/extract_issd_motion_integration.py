"""Preserve the native movement integration and conditional rollback evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asm', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.asm.read_text(encoding='utf-8')
    body = source.split('CODE_80D2B3:', 1)[1].split('CODE_80D33F:', 1)[0]
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
        'limitations': ['The range predicate retains native carry semantics; it is not simplified to a geometric rectangle.', 'Meanings of flags, tail helpers and browser-unit conversion remain unresolved.', 'No browser physics change is authorized by this artifact alone.'],
    }
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
