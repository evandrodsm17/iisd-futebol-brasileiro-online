#!/usr/bin/env python3
"""Verify controller topologies against the repository's SNES source constants.

The declared slots are semantic interpretations of the symbol names; this
checker proves the existence and numeric values, not runtime pad ownership.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "dist/data/issd-controller-topologies.json"
LINE = re.compile(r"^(!Define_ISSD_NumOfPlayers_[A-Z0-9_]+)\s*=\s*\$([0-9A-Fa-f]{4})\s*$", re.M)

def verify(root: Path = ROOT) -> dict:
    payload = json.loads((root / "dist/data/issd-controller-topologies.json").read_text(encoding="utf-8"))
    asm = (root / payload["source"]).read_text(encoding="utf-8")
    symbols = {name: int(value, 16) for name, value in LINE.findall(asm)}
    modes = payload["modes"]
    if len(modes) != 9 or len(symbols) != 9:
        raise ValueError(f"expected exactly nine native topologies, got source={len(symbols)} manifest={len(modes)}")
    seen = set()
    for mode in modes:
        code = mode["code"]
        if not isinstance(code, int) or code in seen or symbols.get(mode["symbol"]) != code:
            raise ValueError("controller symbol/code mismatch: " + str(mode))
        seen.add(code)
        first = mode["first_side_human_ports"]
        second = mode["second_side_human_ports"]
        ports = first + second
        if not all(type(v) is int and 1 <= v <= 4 for v in ports) or len(ports) != len(set(ports)):
            raise ValueError("invalid/duplicate physical controller ports: " + str(mode))
        if (not first) != mode["first_side_cpu"] or (not second) != mode["second_side_cpu"]:
            raise ValueError("human/CPU side assignment mismatch: " + str(mode))
    if seen != set(range(9)):
        raise ValueError("native mode numbers are not contiguous 0..8")
    return {"modes": len(modes), "max_human_ports": max(len(m["first_side_human_ports"]) + len(m["second_side_human_ports"]) for m in modes)}

if __name__ == "__main__":
    result = verify()
    print(f"OK: {result['modes']} native controller modes, up to {result['max_human_ports']} physical ports")
