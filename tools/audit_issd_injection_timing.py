"""Compare fresh vs delayed synthetic ball injection with event timing."""
import argparse,collections,hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(timing,fresh,image):
 rows=[json.loads(x) for x in timing.read_bytes().splitlines()]
 out=[]
 for case in range(1,5):
  selected=[r for r in rows if r['case']==case and r['step']==1]
  def one(site):
   v=[r for r in selected if r['site']==site]
   if len(v)!=1:raise ValueError(f'Missing {site} in case {case}')
   return v[0]
  before,inject,entry,after=map(one,['before','injected','8389E3','after'])
  if (inject['camX']+inject['x']-(inject['camY']+inject['y']))&65535 != 1676:raise ValueError('Injection target mismatch')
  out.append({'case':case,'injection':'before_frame' if case<3 else 'frame_start','advance_before_injection':0 if case in (1,3) else 2,'before_carrier':before['carrier'],'before_ball_type':before['ballType'],'injected_x':inject['x'],'at_integration_x':entry['x'],'frame_end_native_x':after['nativeX'],'integration_80d31a_observed':any(r['site']=='80D31A' for r in selected)})
  if (entry['x']==inject['x'])!=(case in (1,3)):raise ValueError('Unexpected persistence')
 snapshots=[json.loads(x) for x in fresh.read_bytes().splitlines()]
 frames=[r for r in snapshots if r['type']=='frame' and r['phase']==3]
 if len(frames)!=90:raise ValueError('Incomplete camera samples')
 return {'schema':'issd-ball-injection-timing/v1','timing_trace_sha256':sha(timing),'fresh_trace_sha256':sha(fresh),'screenshot_sha256':sha(image),'cases':out,'fresh_90_frames':{'frames':len(frames),'frames_at_target_native_x':sum(r['ball2a']==1676 for r in frames),'camera_x_first':frames[0]['r98'],'camera_x_last':frames[-1]['r98'],'controlled_actor_first':frames[0]['controlled'],'controlled_actor_last':frames[-1]['controlled']},'limitations':['Synthetic memory injections in one saved state; not natural gameplay.','Different ball type and carrier are observed before delayed cases but causality has not been established.','The camera target is unknown and the screenshot is visual evidence only, not a coordinate mapping.','Data at hook entry and frame end have different timings.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('timing',type=Path);p.add_argument('fresh',type=Path);p.add_argument('image',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.timing,a.fresh,a.image);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',len(r['cases']),'timing cases;',r['fresh_90_frames']['frames_at_target_native_x'],'of 90 frames at target')
if __name__=='__main__':main()
