"""Extract direct control-flow references from selected ISSD handler blocks."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
HANDLER=re.compile(r'^(CODE_[0-9A-F]+):')
CALL=re.compile(r'\b(?:JSR|JSL|JMP|BRA|BEQ|BNE|BCC|BCS|BMI|BPL)\.[wlb]?\s+(CODE_[0-9A-F]+)')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('asm',type=Path);p.add_argument('targets',type=Path);p.add_argument('output',type=Path);a=p.parse_args();lines=a.asm.read_text(encoding='utf-8').splitlines();tables=json.loads(a.targets.read_text());wanted={x for t in tables.values() for x in t['targets']};out={}
 for i,line in enumerate(lines):
  h=HANDLER.match(line)
  if not h or h.group(1) not in wanted:continue
  body=[]
  for nxt in lines[i+1:]:
   if HANDLER.match(nxt):break
   body.append(nxt)
  out[h.group(1)]={'flow_targets':sorted({target for text in body for target in CALL.findall(text)})}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
