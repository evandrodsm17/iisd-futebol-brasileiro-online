#!/usr/bin/env python3
"""Diff raw BizHawk team-management snapshots without inventing menu semantics."""
import argparse, json, re
from pathlib import Path

KEYS=("lineup_first","lineup_second","original_snapshot_first","original_snapshot_second")
HEX=re.compile(r"^[0-9A-Fa-f]{40}$")
def analyze(rows):
    events=[]
    previous=None
    for row in rows:
        if not all(HEX.fullmatch(row.get(k,"")) for k in KEYS):
            raise ValueError("Expected four 20-byte WRAM arrays encoded as 40 hex digits")
        if previous and row["frame"]<=previous["frame"]:
            raise ValueError("Frame numbers must strictly increase")
        if previous:
            changed={}
            for name in KEYS:
                before=bytes.fromhex(previous[name]);after=bytes.fromhex(row[name])
                positions=[{"slot":i,"from":before[i],"to":after[i]} for i in range(20) if before[i]!=after[i]]
                if positions:changed[name]=positions
            for key in ("phase","selector_first","selector_second","team_record_a6_first","team_record_a6_second","selected_actor_candidate"):
                if previous[key]!=row[key]:changed[key]={"from":previous[key],"to":row[key]}
            if changed:events.append({"frame":row["frame"],"changed":changed,"input_snapshot":{k:row[k] for k in ("p1_raw_0010","p1_held_0020","p1_pressed_0028")}})
        previous=row
    return {"schema":"issd-team-management-observations/v1","samples":len(rows),"changes":len(events),"events":events,"limitations":["A changed lineup byte is not automatically a substitution.","A changed A6 byte is not independently proven to be a formation selection.","P2 candidate words are not yet verified as pad input.","This report does not infer the original menu state or substitution cap."]}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("trace",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args()
    rows=[json.loads(s) for s in args.trace.read_text(encoding="utf-8").splitlines() if s.strip()]
    result=analyze(rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Processed",result["samples"],"samples,",result["changes"],"changes")
if __name__=="__main__":main()
