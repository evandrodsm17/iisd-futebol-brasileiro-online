"""Export the native player handler-program table without assigning gameplay names."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TABLE = "DATA_81BD58"


def block(lines: list[str], label: str, count: int = 22) -> str:
    start = next((index for index, line in enumerate(lines) if line.startswith(label + ":")), None)
    if start is None:
        raise ValueError(f"missing {label}")
    return "\n".join(lines[start:start + count])


def records(lines: list[str]) -> list[list[str]]:
    start = next((index for index, line in enumerate(lines) if line.startswith(TABLE + ":")), None)
    if start is None:
        raise ValueError(f"missing {TABLE}")
    rows: list[list[str]] = []
    for line in lines[start + 1:]:
        item = line.strip()
        if not item:
            break
        if not item.startswith("dw "):
            raise ValueError(f"unexpected table line: {item}")
        values = [value.strip() for value in item.removeprefix("dw ").split(",")]
        if len(values) != 4:
            raise ValueError(f"expected four words in table record: {item}")
        rows.append(values)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asm", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    lines = args.asm.read_text(encoding="utf-8").splitlines()
    loader = block(lines, "CODE_848548")
    for needle in ("ADC.w #$0008", "LDA.w DATA_81BD58,y", "LDA.w DATA_81BD58+$02,y", "LDA.w DATA_81BD58+$04,y", "LDA.w DATA_81BD58+$06,y"):
        if needle not in loader:
            raise ValueError(f"CODE_84:8548 no longer contains {needle}")
    rows = records(lines)
    if len(rows) != 242:
        raise ValueError(f"unexpected {TABLE} record count: {len(rows)}")
    entries = [{"index": index, "byte_offset": f"${index * 8:04X}", "handler_a": row[0], "handler_b": row[1], "handler_c": row[2], "configuration_word": row[3]} for index, row in enumerate(rows)]
    tracked = {"CODE_84B91E", "CODE_84B999", "CODE_84B9C6"}
    known_rows = [entry for entry in entries if tracked.intersection({entry["handler_a"], entry["handler_b"], entry["handler_c"]})]
    payload = {
        "schema_version": 1,
        "source": {"assembly": str(args.asm), "table": "DATA_81:BD58", "loader": "CODE_84:8548 / CODE_84:854E"},
        "record_layout": {"stride_bytes": 8, "fields": ["handler_a", "handler_b", "handler_c", "configuration_word"]},
        "loader_contract": {"advance": "$32 + $0008", "destination_fields": {"handler_a": "$90", "handler_b": "$92", "handler_c": "$94", "configuration_word": "$60"}},
        "records": entries,
        "known_handler_rows": known_rows,
        "limitations": ["The three handler columns are preserved as native destinations; their actor/control ownership is not named here.", "Record index is table position, not a proven gameplay state label.", "Configuration-word bit semantics and transitions into each record remain pending further static or runtime evidence."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
