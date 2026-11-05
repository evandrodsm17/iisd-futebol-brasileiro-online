"""Audit why three goalkeeper-throw flights leave ball type $0A."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]

def audit(root,reference,state):
 results={}
 for name,direction,frame,actor in (('Side',0,4522,0x0b00),('Up',7,4569,0x1800),('Down',1,4576,0x0800)):
  action=root/name/'B';neutral=root/name/'NEUTRAL'
  for button,folder in (('B',action),('NEUTRAL',neutral)):
   if (folder/'trial.jsonl').read_bytes()!=(reference/name/button/'trial.jsonl').read_bytes():raise ValueError('Trial mismatch against audited reference')
  trace=read(action/'keeper-transfers.jsonl');control=read(neutral/'keeper-transfers.jsonl')
  if not all(any(x.get('type')=='session_end' for x in rows) for rows in (trace,control)):raise ValueError('Incomplete capture')
  events=[x for x in trace if x.get('type')=='ball_vector_hook' and x['frame']==frame and x['address'] in ('8394A4','839E32','839EC3','83953F')]
  if [x['address'] for x in events]!=['8394A4','839E32','839EC3','83953F']:raise ValueError('Unexpected callback order')
  entry,vector,corrected,stored=events
  if entry['x']!=actor or entry['ball_type']!=10 or entry['d']!=0 or vector['ball_type']!=0:raise ValueError('Unexpected reinitialization')
  if any(stored[k]!=0 for k in ('ball_vx','vx_fraction','ball_vy','vy_fraction')):raise ValueError('Expected zero horizontal vector')
  motion=[x for x in trace if x.get('type')=='ball_vector_hook' and x['frame']<frame and x['address']=='839E32' and x['ball_type']==10]
  if not motion:raise ValueError('No earlier throw')
  results[str(direction)]={'frame':frame,'actor_argument':actor,'events':events,
    'action_trial_sha256':sha(action/'trial.jsonl'),'neutral_trial_sha256':sha(neutral/'trial.jsonl'),
    'action_trace_sha256':sha(action/'keeper-transfers.jsonl'),'neutral_trace_sha256':sha(neutral/'keeper-transfers.jsonl')}
 return {'schema':'issd-goalkeeper-flight-reinitialization/v1','state_sha256':sha(state),'directions':results,
  'limitations':['A change of internal type alone does not prove contact or prevent a later bounce.',
   'X carries an actor address into initialization; the observed hooks do not identify the caller or prove physical collision.',
   'These three trials share one saved state and do not represent all goalkeeper throws.',
   'Ground bounce and gradual loss of speed without player interaction remain to be captured.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-vector-products'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-vector-hooks'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: three flight reinitializations audited')
if __name__=='__main__':main()
