"""Export validated ISSD action descriptor tables without inventing OAM data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_locomotion_scripts import byte, decode, word
from extract_issd_catalog import EXPECTED_MD5


# These table roots are referenced by native action handlers or captures.
ACTIONS = {
    "big_kick": 0xD007,
    "big_kick_alternate": 0xD100,
    "slide": 0xDB25,
    "get_up": 0xDB5B,
    "idle": 0xD320,
    "idle_with_ball": 0xD6DB,
    "turn_while_sprinting": 0xD79B,
}


def decode_timed(rom: bytes, script: int, timing_address: int | None = None) -> tuple[list[dict[str, object]], list[int]]:
    """Decode E600/E60C tables using their zero-terminated duration bytes."""
    timing_address = script + 0x10 if timing_address is None else timing_address
    durations = []
    for i in range(64):
        duration = byte(rom, timing_address + i)
        if duration == 0:
            break
        durations.append(duration)
    else:
        raise ValueError(f"missing duration terminator for ${script:04X}")
    if not durations:
        raise ValueError(f"empty duration table for ${script:04X}")
    directions = []
    for direction in range(8):
        pointer = word(rom, script + direction * 2)
        if pointer < 0x8000: raise ValueError('Invalid direction pointer')
        descriptors = [word(rom, pointer + i * 2) | 0x8000 for i in range(len(durations))]
        directions.append({'direction': direction, 'pointer': f'$82:{pointer:04X}', 'descriptors': descriptors})
    return directions, durations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 0x200000 or hashlib.md5(rom).hexdigest() != EXPECTED_MD5:
        raise ValueError("expected the verified 2 MiB headerless USA ROM")
    actions = {}
    for name, address in ACTIONS.items():
        if name in ('slide', 'get_up', 'big_kick', 'big_kick_alternate', 'turn_while_sprinting'):
            timing_address = 0xd017 if name in ('big_kick', 'big_kick_alternate') else (0xd7ab if name == 'turn_while_sprinting' else address + 0x10)
            directions, durations = decode_timed(rom, address, timing_address)
            actions[name] = {'script': f'$82:{address:04X}',
                             'timing': {'kind': 'per_frame', 'ticks': durations,
                                        'source': f'$82:{timing_address:04X}', 'terminator': 0,
                                        'consumer': '$84:E600 / $84:E5D1' if name in ('big_kick', 'big_kick_alternate', 'turn_while_sprinting') else '$84:E60C / $84:E5D1'},
                             'directions': directions}
            if name == 'turn_while_sprinting':
                variants=[]
                for i in range(5):
                    _,variant=decode_timed(rom,address,0xd7ab+i*4)
                    if len(variant)!=len(durations): raise ValueError('Inconsistent turn sequence length')
                    variants.append({'source':f'$82:{0xd7ab+i*4:04X}', 'ticks':variant})
                actions[name]['timing']={'kind':'selected_per_frame','variants':variants,
                                         'selection':'$84:8A1A / $80:E8AD','consumer':'$84:E600 / $84:E5D1'}
        else:
            actions[name] = {'script': f'$82:{address:04X}', 'directions': decode(rom, address)}
    payload = {
        "source": {"rom_md5": hashlib.md5(rom).hexdigest(), "bank": "$82"},
        "limitations": [
            "Action timing and sequence limits reflect the listed native handler paths; other call sites may use other timing tables.",
            "No OAM composition is inferred; nominal timing can be interrupted by gameplay state changes.",
            "Palette selection remains pending a matching runtime frame.",
        ],
        "actions": actions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
