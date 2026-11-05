"""Compare teammates and ball positions after paired goalkeeper throw trials.

Distances are native integer-coordinate observations, not proof of targeting.
"""
import argparse,hashlib,json,math
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def delta(a,b):return ((a-b+32768)%65536)-32768

def snapshots(rows,frame):
 group=[r for r in rows if r.get('type')=='team_sample' and r['frame']==frame]
 if len(group)!=10 or len({r['actor'] for r in group})!=10 or len({r['team'] for r in group})!=1:raise ValueError('Expected ten teammates')
 result=[]
 for r in group:
  dx=delta(r['x'],r['ball_x']);dy=delta(r['y'],r['ball_y'])
  result.append({'actor':r['actor'],'state':r['state'],'script':r['script'],'x':r['x'],'y':r['y'],
    'ball_x':r['ball_x'],'ball_y':r['ball_y'],'dx_to_ball':dx,'dy_to_ball':dy,'distance_squared':dx*dx+dy*dy})
 return sorted(result,key=lambda x:(x['distance_squared'],x['actor']))

def audit(root,reference,state):
 result={}
 for name,direction,release,start in [('Side',0,4473,20),('Up',7,4523,70),('Down',1,4523,70)]:
  a=root/name/'B';n=root/name/'NEUTRAL';traces={}
  for button,folder in [('B',a),('NEUTRAL',n)]:
   if (folder/'trial.jsonl').read_bytes()!=(reference/name/button/'trial.jsonl').read_bytes():raise ValueError('Trial differs from audited reference')
   rows=read(folder/'keeper-transfers.jsonl')
   if not any(r.get('type')=='session_end' for r in rows):raise ValueError('Incomplete trace')
   traces[button]=rows
  # Ensure team samples also agree before the action, not just selected-actor logs.
  trial=read(a/'trial.jsonl');start_frame=next(x['frame'] for x in trial if x.get('step')==start)
  for frame in range(next(x['frame'] for x in trial if x.get('step')==1),start_frame):
   left=snapshots(traces['B'],frame);right=snapshots(traces['NEUTRAL'],frame)
   if left!=right:raise ValueError(f'Teammate baseline differs at {frame}')
  points=[]
  for offset in (0,10,20):
   frame=release+offset
   points.append({'frame':frame,'offset':offset,'action':snapshots(traces['B'],frame),'neutral':snapshots(traces['NEUTRAL'],frame)})
  result[str(direction)]={'case':name,'release_frame':release,'pre_input_team_frames_match':start-1,
    'samples':points,'action_trace_sha256':sha(a/'keeper-transfers.jsonl'),'neutral_trace_sha256':sha(n/'keeper-transfers.jsonl'),
    'action_trial_sha256':sha(a/'trial.jsonl'),'neutral_trial_sha256':sha(n/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-teammate-observation/v1','state_sha256':sha(state),'directions':result,
   'limitations':['Distances use raw integer coordinates and ignore fractional components and height.',
     'Closing distance alone does not distinguish ball motion, player motion, targeting, or collision.',
     'Only three launches from one saved state; not evidence of a universal nearest-player rule.',
     'Actor addresses and states do not prove who will receive or control the ball.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-teammate-trace'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-vector-hooks'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: three teammate trajectories compared with neutral controls')
if __name__=='__main__':main()
