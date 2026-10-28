"""Extract the descriptor-driven dynamic OBJ VRAM upload contract from ISSD."""

import argparse
import json
from pathlib import Path


def block(lines: list[str], label: str, length: int) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + length])


def require(text: str, label: str, *needles: str) -> None:
    for needle in needles:
        if needle not in text:
            raise ValueError(f"{label} no longer contains {needle}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    upload = block(lines, "CODE_84E6C7", 92)
    require(upload, "CODE_84:E6C7",
            "AND.w #$01FF", "ASL", "STA.b $40", "LDA.w #$6000",
            "ADC.b $40", "ADC.w #$0100", "!REGISTER_WriteToVRAMPortLo")
    payload = {
        "schema_version": 1,
        "source": {
            "assembly": str(args.asm),
            "entry": "CODE_84:E6C7",
            "descriptor": "bank $82, six bytes at object+$14",
        },
        "upload": {
            "graphics_source": "descriptor bytes 2..4",
            "destination_vram_word": "$6000 + ((graphics_source_low_word & $01FF) << 4)",
            "first_row": "length-prefixed source row at graphics_source",
            "second_row": "next length-prefixed source row at destination + $0100 VRAM words",
            "queue": "two ten-byte DMA records appended through $7E:0048",
        },
        "limitations": [
            "The extract proves upload addresses and row staging, not a final hardware OAM tile number for every actor.",
            "Object tile-table normalization must be validated against same-frame OAM before generic action sprites are exported.",
            "Uniform-detail upload branches beginning at CODE_84:E77D require separate validation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
