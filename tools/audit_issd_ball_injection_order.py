"""Check where synthetic ball positions stop being observed in an isolated replay."""
import argparse,collections,hashlib,json
from pathlib import Path

def audit(path):
 data=path.read_bytes();rows=[json.loads(line) for line in data.splitlines()]
 frames=[r for r in rows if r['type']=='frame'];pairs=[]
 if len(frames)!=180:raise ValueError('Incomplete 180-frame replay')
 for step in range(1,4):
  scoped=[(i,r) for i,r in enumerate(rows) if r.get('phase')==2 and r.get('step')==step]
  injections=[(i,r) for i,r in scoped if r['type']=='inject']
  entries=[(i,r) for i,r in scoped if r['type']=='hook' and r['site']=='8389E3']
  if len(injections)!=1 or len(entries)!=1:raise ValueError('Missing injection or integration hook')
  start,initial=injections[0];end,first=entries[0]
  if end<=start:raise ValueError('Unexpected record order')
  writes=[r for r in rows[start+1:end] if r['type']=='write' and r['watch'] in (0x407,0x408,0x409,0x40b,0x40c,0x40d,0x7e0407,0x7e0408,0x7e0409,0x7e040b,0x7e040c,0x7e040d)]
  if writes:raise ValueError('A watched CPU write preceded the first hook; inspect it')
  if initial['ball08']==first['ball08']:raise ValueError('Position remained the same')
  pairs.append({'step':step,'injected_ball08':initial['ball08'],'at_8389e3_ball08':first['ball08'],'at_8389e3_saved_x':first['savedX'],'watched_cpu_writes_in_between':len(writes)})
 return {'schema':'issd-ball-injection-order-observation/v1','trace_sha256':hashlib.sha256(data).hexdigest(),'frames':len(frames),'pairs':pairs,'limitations':['One saved state and three sequential frame advances, using synthetic memory writes.','No watched System Bus write before the hook does not exclude other address aliases, emulator timing or core state behavior.','A matching savedX value is correlation only and does not establish which component restored the position.','CPU callback and end-of-frame values must not be treated as simultaneous.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.trace);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',len(r['pairs']),'injection/hook pairs; no watched write in the interval')
if __name__=='__main__':main()
