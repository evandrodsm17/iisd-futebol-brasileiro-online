"""List direct WRAM operands referenced by recovered ISSD dispatch handlers."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
HANDLER=re.compile(r'^(CODE_[0-9A-F]+):')
RAM=re.compile(r'\$([0-9A-F]{4})\b')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('asm',type=Path);p.add_argument('targets',type=Path);p.add_argument('output',type=Path);a=p.parse_args();lines=a.asm.read_text(encoding='utf-8').splitlines();targets=json.loads(a.targets.read_text());wanted={x for table in targets.values() for x in table['targets']};out={}
 for i,line in enumerate(lines):
  hit=HANDLER.match(line)
  if not hit or hit.group(1) not in wanted:continue
  body=[]
  for next_line in lines[i+1:]:
   if HANDLER.match(next_line):break
   body.append(next_line)
  refs=sorted({f'$7E:{value}' for text in body for value in RAM.findall(text)})
  out[hit.group(1)]={'wram_operands':refs,'line_count':len(body)}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__':main()
