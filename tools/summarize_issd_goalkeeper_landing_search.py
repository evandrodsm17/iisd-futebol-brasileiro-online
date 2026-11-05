"""Summarize natural goalkeeper throw landing searches without inferring absence elsewhere."""
import argparse,collections,hashlib,json
from pathlib import Path

EXPECTED={25,35,45,55,70,90,110,120}
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(analysis,state):
 result=[]
 for folder,direction,mask in [('keeper-native-landing-times','Down',0x400),('keeper-native-landing-up','Up',0x800)]:
  roots=list((analysis/folder).iterdir())
  if {int(p.name) for p in roots if p.is_dir()}!=EXPECTED:raise ValueError('Expected eight start times')
  for root in sorted(roots,key=lambda p:int(p.name)):
   start=int(root.name);trial=read(root/'trial.jsonl');trace=read(root/'keeper-transfers.jsonl')
   headers=[x for x in trial if x.get('type')=='session_start'];pre=[x for x in trial if x.get('type')=='pre_direction'];samples={x['step']:x for x in trial if 'step' in x}
   if len(headers)!=1 or len(pre)!=1 or pre[0]['direction']!=direction or headers[0]['start']!=start or headers[0]['button']!='B' or set(samples)!=set(range(1,401)) or not any(x.get('type')=='session_end' and x['steps']==400 for x in trial):raise ValueError('Incomplete trial')
   if any(samples[t]['held_p1']!=mask for t in range(2,start)) or any(samples[t]['held_p1']!=0x8000 or samples[t]['selected']!=0x500 for t in range(start,start+6)):raise ValueError('Input mismatch')
   if not any(x.get('type')=='session_end' for x in trace):raise ValueError('Incomplete observer')
   bounces=[{'frame':x['frame'],'ball_type':x['ball_type']} for x in trace if x.get('type')=='bounce_hook' and x['address']=='838883']
   if any(x['ball_type']==10 for x in bounces):raise ValueError('Type-10 landing candidate requires review')
   result.append({'initial_direction':direction,'action_step':start,'trial_sha256':digest(root/'trial.jsonl'),'trace_sha256':digest(root/'keeper-transfers.jsonl'),'bounces':bounces})
 return {'schema':'issd-goalkeeper-landing-search/v1','state_sha256':digest(state),'trials':result,
  'limitations':['This search covers one initial saved state and the listed controls only.',
    'The observer records the specific bounce path at $83:8883; other ground interactions are not excluded.',
    'No conclusions about impossibility, web-world scale, or general goalkeeper throw physics are warranted.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.analysis,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: 16 input-verified landing-search trials')
if __name__=='__main__':main()
