"""Audit native coordinate translation between ball integration calls."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

CODE=bytes.fromhex('a900045ba50c186da200850c8512a508186da0008508a900055b')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def fixed(row,k):return (row[k]<<16)|row[k+'_frac']
def audit(root,reference,rom_path,state):
 raw=rom_path.read_bytes();head=len(raw)%0x8000
 if head not in (0,512) or hashlib.md5(raw[head:]).hexdigest()!=EXPECTED_MD5 or raw[head+0x1cfcb:head+0x1cfcb+len(CODE)]!=CODE:raise ValueError('Unexpected ROM translation code')
 result={}
 for name,direction in (('Side','0'),('Up','7'),('Down','1')):
  folder=root/name;ref=reference/name/'B'
  if (folder/'trial.jsonl').read_bytes()!=(ref/'trial.jsonl').read_bytes():raise ValueError('Replay differs from paired integration reference')
  rows=read(folder/'keeper-transfers.jsonl')
  if not any(r.get('type')=='session_end' for r in rows):raise ValueError('Incomplete replay')
  intervals=[];translations=0
  for i,r in enumerate(rows):
   if r.get('type')!='world_translation' or r['address']!='83CFCB' or r['ball_type']!=10:continue
   following=[x for x in rows[i+1:] if x.get('type')=='world_translation' and x['frame']==r['frame'] and x['address']=='83CFE5'][:2]
   if len(following)!=2:raise ValueError('Missing actor translation observations')
   first,second=following
   for axis in ('x','y'):
    delta=r['d'+axis]
    if (first['ball_'+axis]-r['ball_'+axis])&0xffff!=delta:raise ValueError('Ball translation mismatch')
    if (second['actor_'+axis]-first['actor_'+axis])&0xffff!=delta:raise ValueError('Actor translation mismatch')
   translations+=1
  for i,r in enumerate(rows):
   if r.get('type')!='ball_integration' or r['address']!='838A1D' or r['ball_type']!=10:continue
   next_entry=next(((j,x) for j,x in enumerate(rows[i+1:],i+1) if x.get('type')=='ball_integration' and x['address']=='8389FB'),None)
   if not next_entry or next_entry[1]['frame']!=r['frame']+1 or next_entry[1]['ball_type']!=10:continue
   j,nxt=next_entry;moving=[x for x in rows[i+1:j] if x.get('type')=='world_translation' and x['address']=='83CFCB']
   if len(moving)!=1:raise ValueError('Unexpected translation count between calls')
   move=moving[0]
   for axis in ('x','y'):
    if ((fixed(nxt,axis)-fixed(r,axis))&0xffffffff)!=((move['d'+axis]<<16)&0xffffffff):raise ValueError('Inter-call difference not explained')
   intervals.append({'frame':r['frame'],'dx':move['dx'],'dy':move['dy']})
  if not intervals:raise ValueError('No consecutive intervals')
  result[direction]={'translation_calls_verified':translations,'intervals_explained':len(intervals),'intervals':intervals,
    'action_trial_sha256':sha(folder/'trial.jsonl'),'action_trace_sha256':sha(folder/'keeper-transfers.jsonl'),
    'paired_reference_sha256':sha(ref/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-world-translation-audit/v1','rom_sha256':hashlib.sha256(raw[head:]).hexdigest(),'state_sha256':sha(state),
  'routine':'$83:CFCB..$83:CFE5','directions':result,
  'limitations':['Translation of ball and actor is observed; the source and semantic purpose of $00A0/$00A2 remain to be established.',
   'Only sampled intervals for one saved state and three launch orientations are covered.',
   'This is not a mapping to web-world scale or a complete model of ball Z, friction and collisions.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-translation'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-ball-integration'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK:',sum(x['intervals_explained'] for x in r['directions'].values()),'intervals explained by shared translation')
if __name__=='__main__':main()
