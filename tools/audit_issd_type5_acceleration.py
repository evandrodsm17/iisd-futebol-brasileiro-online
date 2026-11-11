"""Compare type-5 observed vertical velocity deltas with the ROM lookup."""
import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_catalog import EXPECTED_MD5


def digest(data):
    return hashlib.sha256(data).hexdigest()


def audit(rom, trace, assembly):
    image = rom.read_bytes()
    header = len(image) % 0x8000
    if header not in (0, 512) or hashlib.md5(image[header:]).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    source = assembly.read_text(encoding='utf8')
    routine = source.split('CODE_83941F:', 1)[1].split('CODE_83943D:', 1)[0]
    for op in ('LDA.b $58,x', 'ADC.b $34,x', 'STA.b $34,x', 'LDA.b $36,x', 'ADC.w #$0000', 'STA.b $36,x'):
        if op not in routine:
            raise ValueError('Unexpected vertical update routine')
    raw = trace.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    hooks = [row for row in rows if row['type'] == 'hook' and row['site'] == '85F89B']
    if len(hooks) != 15 or {h['y'] for h in hooks} != set(range(12)):
        raise ValueError('Incomplete sweep')
    trials = []
    for hook in hooks:
        parameter = hook['y']
        acceleration = int.from_bytes(image[header + 0xa27b + 2 * parameter:header + 0xa27d + 2 * parameter], 'little')
        frames = [row for row in rows if row['type'] == 'frame' and row['trial'] == hook['trial'] and row['step'] >= hook['step']]
        changed = unchanged = 0
        for before, after in zip(frames, frames[1:]):
            if after['step'] != before['step'] + 1:
                raise ValueError('Missing frame')
            if before['ballType'] != 5 or after['ballType'] != 5 or before['carrier'] != 0 or after['carrier'] != 0:
                continue
            if before['vz'] < 0x8000 or after['vz'] < 0x8000:
                continue
            a = (before['vz'] << 16) | before['vzFrac']
            b = (after['vz'] << 16) | after['vzFrac']
            delta = (b - a) & 0xffffffff
            if delta == 0:
                unchanged += 1
            elif delta == acceleration:
                changed += 1
            else:
                raise ValueError(f"Unexpected delta in trial {hook['trial']} step {after['step']}: {delta}")
        if not changed:
            raise ValueError(f"No advancing transitions in trial {hook['trial']}")
        trials.append({'trial': hook['trial'], 'parameter': parameter, 'acceleration_word': acceleration,
                       'matching_transitions': changed, 'unchanged_transitions': unchanged})
    return {'schema': 'issd-type5-acceleration-observation/v1', 'rom_sha256': digest(image[header:]),
            'trace_sha256': digest(raw), 'disassembly_sha256': digest(assembly.read_bytes()),
            'source_routine': '83:941F / 83:942E', 'table_offset': '0x00A27B', 'trials': trials,
            'limits': ['One saved state, actor, direction and weather; not a universal gameplay rule.',
                       'Frame-end samples only; unchanged transitions are counted, not explained.',
                       'Only consecutive free type-5 samples with both vertical velocity words negative are compared.',
                       'This does not establish height, landing, web scaling, or horizontal velocity.',
                       'ROM and trace are not distributed.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rom', type=Path)
    parser.add_argument('trace', type=Path)
    parser.add_argument('assembly', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.trace, args.assembly)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {sum(t['matching_transitions'] for t in report['trials'])} matching and {sum(t['unchanged_transitions'] for t in report['trials'])} unchanged transitions")


if __name__ == '__main__':
    main()
