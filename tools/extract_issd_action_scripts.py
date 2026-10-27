"""Export validated ISSD action descriptor tables without inventing OAM data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_locomotion_scripts import decode


# These table roots are referenced by native action handlers or captured in a
# real match. They contain direction pointers only; timing/OAM/palette are
# deliberately not inferred here.
ACTIONS = {
    "big_kick": 0xD007,
    "big_kick_alternate": 0xD100,
    "slide": 0xDB25,
    "get_up": 0xDB5B,
    "idle_with_ball": 0xD6DB,
    "turn_while_sprinting": 0xD79B,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 0x200000:
        raise ValueError("expected a 2 MiB headerless USA ROM")
    payload = {
        "source": {"rom_md5": hashlib.md5(rom).hexdigest(), "bank": "$82"},
        "limitations": [
            "Descriptor order only; no OAM composition is inferred.",
            "No timing interpretation is emitted without its native handler.",
            "Palette selection remains pending a matching runtime frame.",
        ],
        "actions": {
            name: {"script": f"$82:{address:04X}", "directions": decode(rom, address)}
            for name, address in ACTIONS.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
