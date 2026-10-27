"""Extract named indirect-dispatch targets from ISSD disassembly source."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

TABLES={'match_phase':'DATA_83CF86','collision':'DATA_83D77F','trajectory':'DATA_83D9A5','goalkeeper_dive':'DATA_83DCAA','goalkeeper_catch':'DATA_83DDA1'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('asm',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 lines=a.asm.read_text(encoding='utf-8').splitlines();result={}
 for name,label in TABLES.items():
  start=next(i for i,line in enumerate(lines) if line.strip()==label+':')+1;targets=[]
  for line in lines[start:]:
   hit=re.search(r'\bdw\s+(CODE_[0-9A-F]+)',line)
   if not hit: break
   targets.append(hit.group(1))
  result[name]={'label':label,'targets':targets,'count':len(targets)}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
if __name__=='__main__':main()
