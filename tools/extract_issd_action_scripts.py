"""Export validated ISSD action descriptor tables without inventing OAM data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_locomotion_scripts import byte, decode, word
from extract_issd_catalog import EXPECTED_MD5


# These table roots are referenced by native action handlers or captured in a
# real match. They contain direction pointers only; timing/OAM/palette are
# deliberately not inferred here.
ACTIONS = {
    "big_kick": 0xD007,
    "big_kick_alternate": 0xD100,
    "slide": 0xDB25,
    "get_up": 0xDB5B,
    "idle": 0xD320,
    "idle_with_ball": 0xD6DB,
    "turn_while_sprinting": 0xD79B,
}


def decode_timed(rom: bytes, script: int) -> tuple[list[dict[str, object]], list[int]]:
    """Decode E60C tables: one duration per pose, then a zero duration."""
    durations = []
    for i in range(64):
        duration = byte(rom, script + 0x10 + i)
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
        if name in ('slide', 'get_up'):
            directions, durations = decode_timed(rom, address)
            actions[name] = {'script': f'$82:{address:04X}',
                             'timing': {'kind': 'per_frame', 'ticks': durations,
                                        'terminator': 0, 'consumer': '$84:E60C / $84:E5D1'},
                             'directions': directions}
        else:
            actions[name] = {'script': f'$82:{address:04X}', 'directions': decode(rom, address)}
    payload = {
        "source": {"rom_md5": hashlib.md5(rom).hexdigest(), "bank": "$82"},
        "limitations": [
            "Slide and get-up use the E60C duration table; other action lists require separate validation and may overread.",
            "No OAM composition is inferred; nominal timing can be interrupted by gameplay state changes.",
            "Palette selection remains pending a matching runtime frame.",
        ],
        "actions": actions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
