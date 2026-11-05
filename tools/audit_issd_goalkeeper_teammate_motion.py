"""Compare teammate movement with shared native translation removed."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def s16(x):return x-65536 if x>=32768 else x
def s32(x):
 x &= 0xffffffff
 return x-0x100000000 if x&0x80000000 else x

def audit(root,reference,state):
 results={}
 for name,direction,release,start in [('Side','0',4473,20),('Up','7',4523,70),('Down','1',4523,70)]:
  captured={};refs={}
  for button in ('B','NEUTRAL'):
   folder=root/name/button;ref=reference/name/button
   if (folder/'trial.jsonl').read_bytes()!=(ref/'trial.jsonl').read_bytes():raise ValueError('Trial reference mismatch')
   rows=read(folder/'keeper-transfers.jsonl');old=read(ref/'keeper-transfers.jsonl')
   if not any(x.get('type')=='session_end' for x in rows):raise ValueError('Incomplete trace')
   samples=[r for r in rows if r.get('type')=='team_sample'];old_samples=[r for r in old if r.get('type')=='team_sample']
   if samples!=old_samples:raise ValueError('Team samples differ from earlier capture')
   captured[button]=rows;refs[button]=folder
  actor_set={r['actor'] for r in captured['B'] if r.get('type')=='team_sample' and r['frame']==release}
  if len(actor_set)!=10:raise ValueError('Expected ten teammates')
  comparisons=[]
  for actor in sorted(actor_set):
   record={'actor':actor}
   for button,key in [('B','action'),('NEUTRAL','neutral')]:
    rows=captured[button];points=[r for r in rows if r.get('type')=='team_sample' and r['actor']==actor and r['frame'] in (release,release+10)]
    if len(points)!=2 or [r['frame'] for r in points]!=[release,release+10]:raise ValueError('Missing team samples')
    first,last=points;translations=[r for r in rows if r.get('type')=='world_translation' and r['address']=='83CFCB' and release<=r['frame']<release+10]
    delta={}
    for axis in ('x','y'):
     origin=(first[axis]<<16)|first[axis+'_frac'];end=(last[axis]<<16)|last[axis+'_frac']
     shift=sum(s16(r['d'+axis]) for r in translations)
     delta[axis]=s32(end-origin-(shift<<16))
    record[key]={'movement_x_16_16':delta['x'],'movement_y_16_16':delta['y'],
      'translation_callbacks':len(translations),'state_before':first['state'],'state_after':last['state'],
      'selected_before':first['selected'],'selected_after':last['selected']}
   comparisons.append(record)
  trials={button:{x['frame']:x for x in read(refs[button]/'trial.jsonl') if 'step' in x} for button in ('B','NEUTRAL')}
  changes=[];last_selection=None
  for frame in range(release,release+21):
   sample=[r for r in captured['B'] if r.get('type')=='team_sample' and r['frame']==frame]
   neutral=[r for r in captured['NEUTRAL'] if r.get('type')=='team_sample' and r['frame']==frame]
   if len(sample)!=10 or len(neutral)!=10:raise ValueError('Missing frame')
   selected={r['selected'] for r in sample};neutral_selected={r['selected'] for r in neutral}
   if len(selected)!=1 or len(neutral_selected)!=1:raise ValueError('Ambiguous selected actor')
   selected=selected.pop()
   if selected!=last_selection:
    def dist(r):
     dx=s16((r['x']-r['ball_x'])&0xffff);dy=s16((r['y']-r['ball_y'])&0xffff)
     return dx*dx+dy*dy
    nearest=min(sample,key=lambda r:(dist(r),r['actor']))
    if trials['B'][frame]['held_p1']!=0 or trials['NEUTRAL'][frame]['held_p1']!=0:raise ValueError('Unexpected held input during selection')
    changes.append({'frame':frame,'held_p1':0,'selected':selected,'neutral_selected':neutral_selected.pop(),
       'nearest_teammate':nearest['actor'],'nearest_distance_squared':dist(nearest),
       'selected_distance_squared':next((dist(r) for r in sample if r['actor']==selected),None)})
    last_selection=selected
  results[direction]={'case':name,'release_frame':release,'interval_frames':10,'movements':comparisons,'selection_changes':changes,
   'action_trace_sha256':sha(refs['B']/'keeper-transfers.jsonl'),'neutral_trace_sha256':sha(refs['NEUTRAL']/'keeper-transfers.jsonl')}
 return {'schema':'issd-goalkeeper-teammate-motion-audit/v1','state_sha256':sha(state),'directions':results,
  'limitations':['Subtracts observed shared translation, but remaining displacement can include AI, physics or other state changes.',
    'Selection changes do not prove automatic recipient targeting; input routing and eligibility remain unverified.',
    'Nearest comparison uses integer horizontal coordinates, ignores height, eligibility and interception prediction.',
    'Three launches from one saved state do not establish general behavior.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-teammate-translation'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-teammate-trace'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: teammate motion corrected for observed shared translation')
if __name__=='__main__':main()
