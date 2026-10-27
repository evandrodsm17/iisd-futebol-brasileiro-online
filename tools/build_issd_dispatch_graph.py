"""Create a subsystem-labelled control-flow graph from recovered handlers."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('tables',type=Path);p.add_argument('flow',type=Path);p.add_argument('output',type=Path);a=p.parse_args();tables=json.loads(a.tables.read_text());flow=json.loads(a.flow.read_text());nodes=[];edges=[]
 for system,table in tables.items():
  for handler in sorted(set(table['targets'])):
   nodes.append({'id':handler,'system':system})
   for target in flow.get(handler,{}).get('flow_targets',[]):edges.append({'from':handler,'to':target,'system':system})
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'nodes':nodes,'edges':edges},indent=2),encoding='utf-8')
if __name__=='__main__':main()
