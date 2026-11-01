#!/usr/bin/env python3
"""Validate bank-84 spatial branches against the original ISS Deluxe assembly.

Static classification ONLY: not proof of passes, crosses or shots.
"""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"YFs_InternationalSuperstarSoccerDeluxe_Disassembly"/"International_Superstar_Soccer_Deluxe"/"Routine_Macros_ISSD.asm"
MANIFEST=ROOT/"dist/data/issd-cpu-spatial-branches.json"

def require(ok,reason):
    if not ok: raise AssertionError("bank-84 ROM evidence changed: "+reason)

def section(asm,start,end):
    a=asm.find(start+":");b=asm.find(end+":",a+len(start)+1)
    require(a>=0 and b>a,"missing ordered labels "+start+"/"+end)
    return asm[a:b]

def words(asm,start,end):
    block=section(asm,start,end)
    found=[]
    for row in block.splitlines():
        if row.lstrip().startswith("dw "):
            found.extend(int(v,16) for v in re.findall(r"\$([A-Fa-f0-9]{4})",row))
    return found

def verify(asm,report):
    expected={
        "DATA_81CFBF":("DATA_81CFCB",[12,24,12,24,16,32]),
        "DATA_81CFE3":("DATA_81CFEF",[32,64,32,64,16,32]),
        "DATA_81CFEF":("DATA_81CFFB",[48,96,48,96,16,32]),
        "DATA_81C99D":("DATA_81C9A7",[0,0,384,896,1152]),
        "DATA_81CD40":("DATA_81CD4A",[768,640,512,384,256]),
        "DATA_81CD4A":("DATA_81CD68",[1536,1280,1024,768,512,40,80,32,64,24,48,16,32,12,24])
    }
    for label,(end,values) in expected.items():
        require(words(asm,label,end)==values,label+" data")
        rows=report["rectangles"]+report["tier_tables"]
        row=next((r for r in rows if r["label"]==label),None)
        require(row is not None and (row.get("bounds") or row.get("raw"))==values,label+" report")
    branch=section(asm,"CODE_84C85D","CODE_84C950")
    for token in ["LDA.w $00CC,y","ASL","CMP.w DATA_81C99D,x",
                  "CMP.w DATA_81CD40,x","CMP.w DATA_81CD4A,x",
                  "LDY.w #DATA_81CFBF","LDY.w #DATA_81CFE3",
                  "LDY.w #DATA_81CFEF","JSR.w CODE_84E925",
                  "JSL.l CODE_80F46D","JSL.l CODE_80DE35",
                  "JSL.l CODE_80D058","JSL.l CODE_80D047",
                  "JMP.w CODE_84C800"]:
        require(token in branch,"branch "+token)
    comparator=section(asm,"CODE_84E925","ADDR_84E94C")
    for token in ["LDA.w DATA_81CFBF&$FF0000,y","SBC.w $0008,x",
                  "SBC.w $000C,x","SBC.w (DATA_81CFBF&$FF0000)+$02,y",
                  "SBC.w (DATA_81CFBF&$FF0000)+$06,y"]:
        require(token in comparator,"spatial compare "+token)
    ball=section(asm,"CODE_84C950","CODE_84CA54")
    for token in ["LDA.w $0410","CMP.w #$FFC0","CMP.w #$FFA0",
                  "LDX.w #$1000","LDX.w #$2000","LDX.w #$4000"]:
        require(token in ball,"ball/air gating "+token)
    return {"rectangles":3,"tier_tables":3,"ball_height_thresholds":[-64,-96],
            "status":"static bounds verified; action semantics unknown"}

if __name__=="__main__":
    print(json.dumps(verify(SOURCE.read_text(encoding="utf-8",errors="replace"),
                            json.loads(MANIFEST.read_text(encoding="utf-8"))),ensure_ascii=False))
