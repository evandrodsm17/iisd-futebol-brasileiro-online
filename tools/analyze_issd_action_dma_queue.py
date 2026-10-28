"""Correlate captured ISSD DMA queue records with descriptor graphics rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def lorom_offset(address: int) -> int:
    if address & 0xFFFF < 0x8000:
        raise ValueError(f"not a LoROM address: ${address:06X}")
    return ((address >> 16) & 0x7F) * 0x8000 + (address & 0x7FFF)


def word(data: bytes, offset: int) -> int:
    return data[offset] | data[offset + 1] << 8


def row_sources(rom: bytes, descriptor: int) -> list[int]:
    start = lorom_offset(0x820000 | descriptor)
    source = rom[start + 2] | rom[start + 3] << 8 | rom[start + 4] << 16
    sources = []
    for _ in range(2):
        header = lorom_offset(source)
        length = word(rom, header)
        if not length or length > 0x100 or length % 2:
            raise ValueError(f"invalid graphics row for descriptor ${descriptor:04X}")
        sources.append(source + 2)
        source += 2 + length
    return sources


def auxiliary_upload(rom: bytes, descriptor: int, actor: dict) -> dict:
    """Return the exact CODE_98:FB86 DMA values when captured actor fields fit."""
    start = lorom_offset(0x820000 | descriptor)
    enable = word(rom, start + 6)
    selector = rom[start + 8]
    if not enable:
        return {"enabled": False}
    table_index = actor.get("animation_timer")
    cursor = actor.get("animation_cursor")
    if table_index is None or cursor is None or table_index > 0x30 or table_index % 4:
        return {"enabled": True, "status": "missing-or-invalid-actor-context"}
    table = lorom_offset(0x81ED6D + table_index)
    base = rom[table] | rom[table + 1] << 8 | rom[table + 2] << 16
    offset = ((selector - 1) & 0xFFFF) << 5
    source = (base & 0xFF0000) | (((base & 0xFFFF) + offset) & 0xFFFF)
    return {
        "enabled": True,
        "selector": selector,
        "source": source,
        "destination_word": (0x6000 + ((cursor & 0xFFFF) << 4)) & 0xFFFF,
        "size": 0x20,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--script", type=lambda value: int(value, 0))
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    rows = [json.loads(line) for line in args.trace.read_text(encoding="utf-8").splitlines() if line]
    if args.script is not None:
        rows = [row for row in rows if row["actor"]["animation_script"] == args.script]
    results = []
    for row in rows:
        actor = row["actor"]
        expected = row_sources(rom, actor["descriptor"])
        queue = row.get("dma_vram_queue")
        if queue is None:
            results.append({"descriptor": f"${actor['descriptor']:04X}", "status": "legacy-trace-without-dma-queue"})
            continue
        entries = queue.get("entries", [])
        matches = []
        for source in expected:
            matching = [entry for entry in entries if entry["source"] == source]
            matches.append({"source": f"${source:06X}", "matches": matching})
        auxiliary = auxiliary_upload(rom, actor["descriptor"], actor)
        if auxiliary.get("enabled") and "source" in auxiliary:
            auxiliary_matches = [
                entry for entry in entries
                if entry["source"] == auxiliary["source"]
                and entry["destination_word"] == auxiliary["destination_word"]
                and entry["size"] == auxiliary["size"]
            ]
            auxiliary = {
                **auxiliary,
                "source": f"${auxiliary['source']:06X}",
                "destination_word": f"${auxiliary['destination_word']:04X}",
                "matches": auxiliary_matches,
            }
        results.append({
            "descriptor": f"${actor['descriptor']:04X}",
            "direction": actor["direction"],
            "queue_bytes": queue.get("bytes"),
            "rows": matches,
            "auxiliary": auxiliary,
        })
    payload = {
        "source": {"kind": "passive_runtime_action_vram_capture", "routine": "CODE_84:E6C7", "queue": "$7E:3200; count $0048"},
        "limitations": ["A zero/absent queue does not disprove a descriptor; capture timing may have crossed NMI.", "Auxiliary equality tests the captured actor+$16/$1A values against CODE_98:FB86; it does not assign a visual OAM role."],
        "records": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(results), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
