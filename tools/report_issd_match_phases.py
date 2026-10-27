"""Summarise phases observed in an ISSD natural-play JSONL trace."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 rows=[]
 for line in a.trace.read_text(encoding='utf-8').splitlines():
  try: rows.append(json.loads(line))
  except json.JSONDecodeError: pass
 phases=Counter(row.get('phase') for row in rows if 'phase' in row)
 transitions=[];previous=None
 for row in rows:
  phase=row.get('phase')
  if phase is not None and phase!=previous: transitions.append({'frame':row['frame'],'phase':phase});previous=phase
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps({'evidence':'runtime-match-trace','samples':len(rows),'phases':{str(k):v for k,v in sorted(phases.items())},'transitions':transitions},indent=2),encoding='utf-8')
if __name__=='__main__':main()
