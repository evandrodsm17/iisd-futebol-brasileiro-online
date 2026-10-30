#!/usr/bin/env python3
"""Recheck native CPU difficulty, RNG, and kick index evidence against 65C816."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe"
ASM = BASE / "Routine_Macros_ISSD.asm"
DEFINES = BASE / "Misc_Defines_ISSD.asm"
REPORT = ROOT / "dist/data/issd-cpu-difficulty-routing.json"

def require(value, reason):
    if not value:
        raise AssertionError("ROM contract changed: " + reason)

def block(text, start, end):
    a, b = text.find(start + ":"), text.find(end + ":")
    require(0 <= a < b, "missing labels " + start + " / " + end)
    return text[a:b]

def verify(asm, defines, report):
    modes = [(int(n, 16), name) for name, n in re.findall(
        r"^!Define_ISSD_NumOfPlayers_([A-Za-z0-9_]+)\s*=\s*\$([0-9A-Fa-f]{4})",
        defines, flags=re.M)]
    modes.sort()
    require(len(modes) == 9 and [n for n, _ in modes] == list(range(9)), "nine modes")
    table = block(asm, "DATA_81AEEF", "DATA_81AF01")
    values = [int(match, 16) for row in table.splitlines() if row.strip().startswith("db ")
              for match in re.findall(r"\$([0-9A-Fa-f]{2})", row)]
    require(len(values) == 18 and set(values) == {0, 2}, "CPU flags table")
    for num, name in modes:
        entry = report["modes"][num]
        require(entry["code"] == num and entry["symbol"].endswith(name), "mode "+name)
        for side in (0, 1):
            cell = entry["sides"][side]
            flag = values[2*num + side]
            require(cell["flag"] == "$"+format(flag, "02X"), "side flag")
            require(cell["team_local_CC"] == ("CurrentGameLevel" if flag else "2"), "side CC")
    region = block(asm, "CODE_83C3C3", "CODE_83C4AC")
    for token in ("LDA.w DATA_81AEEF,y", "LDA.w DATA_81AEEF+$01,y",
                  "LDA.w #$0D00", "LDA.w #$0E00",
                  "JSR.w CODE_83C431", "LDX.w #$0002",
                  "BIT.w #$0002", "LDX.w !RAM_ISSD_InGame_CurrentGameLevel",
                  "STX.b $CC"):
        require(token in region, "difficulty route " + token)
    rng = block(asm, "CODE_8583F3", "CODE_858409")
    for token in ("LDA.w $1FEA", "ROR", "ADC.w $1FEC", "STA.w $1FEC",
                  "STX.w $1FEA"):
        require(token in rng, "RNG " + token)
    for a, b, mask in (("CODE_858409","CODE_858411",1),
                        ("CODE_858411","CODE_858419",3),
                        ("CODE_858419","CODE_858421",7),
                        ("CODE_858421","CODE_858429",15)):
        wrapper = block(asm, a, b)
        require("JSL.l CODE_8583F3" in wrapper and
                "AND.w #$" + format(mask, "04X") in wrapper, "RNG mask")
    kick = block(asm, "CODE_84B9A0", "CODE_84B9C6")
    for token in ("LDA.b $6E","AND.w #$0001","STA.b $2E",
                  "JSL.l CODE_80DD82", "CPX.w #$0005",
                  "DATA_82D007", "DATA_82D100"):
        require(token in kick, "kick selector " + token)
    idx = block(asm, "CODE_80DD82", "CODE_80DD91")
    require(all(t in idx for t in ("ASL", "ADC.b $5A", "TAX")), "index calc")
    return {"modes":len(modes),"cpu_sides":sum(v==2 for v in values),
            "rng_masks":[1,3,7,15],"kick_index_threshold":5}

if __name__ == "__main__":
    result = verify(ASM.read_text(encoding="utf-8",errors="replace"),
                    DEFINES.read_text(encoding="utf-8"),
                    json.loads(REPORT.read_text(encoding="utf-8")))
    print("OK: native ROM level, PRNG and kick-selector contract:", result)
