"""Audit observed B-release events in two directed goalkeeper trials."""
import argparse,hashlib,json
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def s16(x):return x if x<32768 else x-65536

def audit(root,graphics,state):
 result={}
 for name,direction,velocity in (('Up',7,(2,-3,-3)),('Down',1,(5,2,-3))):
  a=root/name/'B';n=root/name/'NEUTRAL';ga=graphics/name/'B';gn=graphics/name/'NEUTRAL'
  if (a/'trial.jsonl').read_bytes()!=(ga/'trial.jsonl').read_bytes() or (n/'trial.jsonl').read_bytes()!=(gn/'trial.jsonl').read_bytes():raise ValueError('Capture trial does not match reference')
  ar=read(a/'trial.jsonl');nr=read(n/'trial.jsonl');aa={r['step']:r for r in ar if 'step' in r};nn={r['step']:r for r in nr if 'step' in r}
  if set(aa)!=set(range(1,181)) or set(nn)!=set(aa):raise ValueError('Incomplete trials')
  headers=[next(x for x in rows if x.get('type')=='session_start') for rows in (ar,nr)]
  pre=[next(x for x in rows if x.get('type')=='pre_direction') for rows in (ar,nr)]
  if pre[0]!=pre[1] or pre[0]['direction']!=name or [x['button'] for x in headers]!=['B','NEUTRAL'] or any(x['start']!=70 or x['duration']!=6 for x in headers):raise ValueError('Trial settings mismatch')
  if any(aa[t]!=nn[t] for t in range(1,70)):raise ValueError('Pre-input state differs')
  if any(aa[t]['selected']!=0x500 or aa[t]['held_p1']!=0x8000 or nn[t]['held_p1']!=0 for t in range(70,76)):raise ValueError('Input mismatch')
  ah=read(a/'keeper-transfers.jsonl');nh=read(n/'keeper-transfers.jsonl')
  if not all(any(x.get('type')=='session_end' for x in rows) for rows in (ah,nh)):raise ValueError('Incomplete hook traces')
  hooks=[x for x in ah if x.get('type')=='release_hook' and x['address']=='85EE38']
  if len(hooks)!=1 or (hooks[0]['frame'],hooks[0]['actor'],hooks[0]['direction'],hooks[0]['link_a6'])!=(4522,0x500,direction,0x500):raise ValueError('Unexpected release hook')
  if any(x.get('type')=='release_hook' and x['address']=='85EE38' for x in nh):raise ValueError('Release in neutral control')
  gen=[x for x in ah if x.get('type')=='release_hook' and x['address']=='85F8B9' and x['frame']==4522 and x['actor']==0x500]
  if len(gen)!=1:raise ValueError('Generic release hook missing')
  before=aa[79];after=aa[80];control=nn[80]
  if before['frame']!=4522 or after['frame']!=4523 or before['link_a6']!=0x500 or after['link_a6']!=0 or control['link_a6']!=0x500:raise ValueError('Unexpected link transition')
  if tuple(s16(after[x]) for x in ('ball_vx','ball_vy','ball_vz'))!=velocity or any(s16(control[x]) for x in ('ball_vx','ball_vy','ball_vz')):raise ValueError('Unexpected velocity')
  motion=[x for x in aa.values() if x['script'] in (0xe625,0xe644)]
  if not motion or motion[0]['frame']!=4517 or after['frame']-motion[0]['frame']!=6:raise ValueError('Sequence offset mismatch')
  result[str(direction)]={'input_direction':name,'pre_input_samples_match':69,'hook_frame':hooks[0]['frame'],'hook':hooks[0],
    'release_frame':after['frame'],'sequence_tick_zero_based':6,'velocity_signed':list(velocity),'neutral_velocity_signed':[0,0,0],
    'action_trial_sha256':digest(a/'trial.jsonl'),'neutral_trial_sha256':digest(n/'trial.jsonl'),
    'action_hook_sha256':digest(a/'keeper-transfers.jsonl'),'neutral_hook_sha256':digest(n/'keeper-transfers.jsonl')}
 return {'schema':'issd-goalkeeper-directed-release-audit/v1','state_sha256':digest(state),'directions':result,
  'limitations':['Only these two states and directions; recorded fields do not prove hidden state equality.',
   'Hook entries occur before execution and do not independently prove the routine returned.',
   'Signed velocity words are not calibrated physical units; no general mechanics are inferred.',
   'Correspondence between ROM direction indices and screen direction remains unverified.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-directed-release'));p.add_argument('--graphics',type=Path,default=Path('analysis/keeper-directed-graphics'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.graphics,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: two paired directed goalkeeper releases')
if __name__=='__main__':main()
