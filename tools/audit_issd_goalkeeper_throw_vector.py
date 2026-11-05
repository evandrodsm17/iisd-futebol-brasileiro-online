"""Audit goalkeeper throw vector inputs against ROM tables and paired trials."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import span

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def sign(x):return x if x<32768 else x-65536

def audit(root,analysis,rom_path,state):
 original=rom_path.read_bytes();head=len(original)%0x8000
 if head not in (0,512) or hashlib.md5(original[head:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 rom=original[head:];out={}
 cases=[('Side',0,4472,4,88,(4,0,-3),analysis/'keeper-release-hooks'),
        ('Up',7,4522,5,96,(2,-3,-3),analysis/'keeper-directed-release'/'Up'),
        ('Down',1,4522,5,96,(5,2,-3),analysis/'keeper-directed-release'/'Down')]
 for name,direction,frame,param,table_value,velocity,reference in cases:
  action=root/name/'B';neutral=root/name/'NEUTRAL'
  for button,folder in (('B',action),('NEUTRAL',neutral)):
   if (folder/'trial.jsonl').read_bytes()!=(reference/button/'trial.jsonl').read_bytes():raise ValueError('Trial differs from paired audited reference')
  events=read(action/'keeper-transfers.jsonl');control=read(neutral/'keeper-transfers.jsonl')
  if not all(any(x.get('type')=='session_end' for x in rs) for rs in (events,control)):raise ValueError('Incomplete hook trace')
  def at(rs,address):return [r for r in rs if r.get('type')=='ball_vector_hook' and r['frame']==frame and r['address']==address]
  init=at(events,'8394A4');vector=at(events,'839E32')
  if len(init)!=1 or len(vector)!=1 or at(control,'8394A4') or at(control,'839E32'):raise ValueError('Unexpected hook sequence')
  init=init[0];vector=vector[0];angle=span(rom,0x819632+direction,1)[0]
  if init['d']!=0 or init['x']!=0x500 or init['a']&63!=angle or init['y']!=param:raise ValueError('Initialization registers differ from ROM direction')
  if vector['d']!=0 or vector['a']!=angle or vector['angle']!=angle or vector['parameter']!=param or vector['ball_type']!=10:raise ValueError('Vector arguments differ')
  if vector['table_value']!=table_value or vector['y']!=table_value or span(rom,0x81a367+10*16+param,1)[0]!=table_value:raise ValueError('ROM parameter differs')
  trial={x['frame']:x for x in read(action/'trial.jsonl') if 'step' in x};control_trial={x['frame']:x for x in read(neutral/'trial.jsonl') if 'step' in x}
  after=trial[frame+1];no=control_trial[frame+1]
  if after['link_a6']!=0 or no['link_a6']!=0x500 or tuple(sign(after[k]) for k in ('ball_vx','ball_vy','ball_vz'))!=velocity:raise ValueError('Release sample differs')
  if any(sign(no[k]) for k in ('ball_vx','ball_vy','ball_vz')):raise ValueError('Neutral ball velocity differs')
  out[str(direction)]={'frame':frame,'actor':init['x'],'rom_angle':angle,'parameter':param,'table_value':table_value,
     'initialization_hook':init,'vector_hook':vector,'observed_velocity_signed':list(velocity),
     'action_trace_sha256':sha(action/'keeper-transfers.jsonl'),'neutral_trace_sha256':sha(neutral/'keeper-transfers.jsonl'),
     'action_trial_sha256':sha(action/'trial.jsonl'),'neutral_trial_sha256':sha(neutral/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-throw-vector-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'state_sha256':sha(state),
   'rom_angle_table':'$81:9632','rom_parameter_table':'$81:A367','ball_type':10,'directions':out,
   'limitations':['Hooks observe routine entry, before the vector calculation returns.',
     'One state, one actor, and three orientations; no general distribution of strengths is established.',
     'Values are ROM units; no mapping to browser pixels or physical speed is established.',
     'Mode 7 multiplication and subsequent ball updates must be validated before porting physics.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-vector-hooks'));p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.analysis,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: three goalkeeper vector inputs match ROM and paired trials')
if __name__=='__main__':main()
