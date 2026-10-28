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
    # The DMA size/destination writes occur after descriptor lookup and the
    # selector calculation, so keep the complete routine through CODE_98FC0E.
    auxiliary = block(lines, "CODE_98FB86", 60)
    auxiliary_scheduler = block(lines, "CODE_98FB34", 45)
    require(upload, "CODE_84:E6C7",
            "AND.w #$01FF", "ASL", "STA.b $40", "LDA.w #$6000",
            "ADC.b $40", "ADC.w #$0100", "!REGISTER_WriteToVRAMPortLo")
    require(auxiliary, "CODE_98:FB86",
            "(DATA_82A3D7&$FF0000)+$06,x", "(DATA_82A3D7&$FF0000)+$08,x",
            "LDA.w #$0020", "LDA.w #$6000", "STA.l $7E0006,x")
    require(auxiliary_scheduler, "CODE_98:FB34",
            "#$0AA0", "#$0AD0", "#$0BA0", "#$0BD0", "#$0CA0", "#$0CD0",
            "JSR.w CODE_98FB86")
    payload = {
        "schema_version": 1,
        "source": {
            "assembly": str(args.asm),
            "entry": "CODE_84:E6C7",
            "descriptor": "bank $82, nine-byte DATA_82:A3D7 record at object+$14; CODE_84:E6C7 consumes bytes 0..5",
        },
        "upload": {
            "graphics_source": "descriptor bytes 2..4",
            "destination_vram_word": "$6000 + ((graphics_source_low_word & $01FF) << 4)",
            "first_row": "length-prefixed source row at graphics_source",
            "second_row": "next length-prefixed source row at destination + $0100 VRAM words",
            "queue": "two ten-byte DMA records appended through $7E:0048",
        },
        "auxiliary_upload": {
            "enable": "descriptor bytes 6..7; only a nonzero value permits upload (the value is not used as an address)",
            "selector": "descriptor byte 8; (selector - 1) << 5 indexes a 32-byte source",
            "source_banks": "direct-page $16 selects a four-byte entry in DATA_81:ED6D; it lists 13 bases DATA_97:CD58 + n*$0300",
            "size_bytes": 32,
            "destination_vram_word": "$6000 + (actor context $1A << 4)",
            "queue": "one ten-byte DMA record appended through $7E:0048 by CODE_98:FB86",
            "gates": "CODE_98:FB34 schedules contexts $0AA0, $0AD0, $0BA0, $0BD0, $0CA0 and $0CD0; CODE_98:FB86 skips when $001E is nonzero or descriptor $0014 equals its prior $14",
        },
        "limitations": [
            "The extract proves upload addresses and row staging, not a final hardware OAM tile number for every actor.",
            "Object tile-table normalization must be validated against same-frame OAM before generic action sprites are exported.",
            "Uniform-detail upload branches beginning at CODE_84:E77D require separate validation.",
            "The visual role and final OAM tile mapping of the auxiliary 32-byte upload are not assigned by this extract.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
