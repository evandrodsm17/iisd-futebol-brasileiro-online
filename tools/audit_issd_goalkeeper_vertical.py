"""Audit the airborne vertical branch of goalkeeper throws in native 16.16."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def fixed(row,integer,fraction):return (row[integer]<<16)|row[fraction]

def audit(root,reference,rom_path,state):
 raw=rom_path.read_bytes();head=len(raw)%0x8000
 if head not in (0,512) or hashlib.md5(raw[head:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 for off,code in ((0x1882a,'18b50e7534950eb5107536'),(0x18863,'951060'),(0x1942e,'b5581875349534b536690000953660')):
  if raw[head+off:head+off+len(bytes.fromhex(code))]!=bytes.fromhex(code):raise ValueError('Unexpected vertical instructions')
 result={}
 for name,direction in (('Side','0'),('Up','7'),('Down','1')):
  folder=root/name;ref=reference/name/'B'
  if (folder/'trial.jsonl').read_bytes()!=(ref/'trial.jsonl').read_bytes():raise ValueError('Reference trial mismatch')
  rows=read(folder/'keeper-transfers.jsonl')
  if not any(r.get('type')=='session_end' for r in rows):raise ValueError('Incomplete capture')
  groups={}
  for r in rows:
   if r.get('type')=='ball_vertical' and r['ball_type']==10:
    groups.setdefault(r['frame'],[]).append(r)
  verified=[]
  for frame,events in sorted(groups.items()):
   names=[r['address'] for r in events]
   if names!=['83941F','83942E','83882A','838863','838865']:raise ValueError('Unexpected vertical path')
   entry,accel,before,store,after=events
   if any(x['xreg']!=0x400 or x['link_a6']!=0 for x in events):raise ValueError('Unexpected ball context')
   velocity=(fixed(accel,'vz','vz_frac')+accel['gravity'])&0xffffffff
   if fixed(before,'vz','vz_frac')!=velocity or accel['gravity']!=before['gravity']:raise ValueError('Acceleration mismatch')
   position=(fixed(before,'z','z_frac')+velocity)&0xffffffff
   if not (position&0x80000000):raise ValueError('Ground/bounce branch excluded')
   if store['a']!=(position>>16) or fixed(after,'z','z_frac')!=position:raise ValueError('Height integration mismatch')
   verified.append({'frame':frame,'before_acceleration':{'vz':accel['vz'],'vz_frac':accel['vz_frac'],'gravity':accel['gravity']},
       'before_height':{'z':before['z'],'z_frac':before['z_frac'],'vz':before['vz'],'vz_frac':before['vz_frac']},
       'after_height':{'z':after['z'],'z_frac':after['z_frac']}})
  if not verified:raise ValueError('No airborne cases')
  result[direction]={'airborne_steps':len(verified),'first':verified[0],'last':verified[-1],
   'trace_sha256':sha(folder/'keeper-transfers.jsonl'),'trial_sha256':sha(folder/'trial.jsonl'),'reference_trial_sha256':sha(ref/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-airborne-vertical-audit/v1','rom_sha256':hashlib.sha256(raw[head:]).hexdigest(),'state_sha256':sha(state),'directions':result,
  'limitations':['Only the observed airborne negative-height branch for ball type 10; landing, bounce and alternate modes are excluded.',
   'The gravitational word is the recorded native value, not a browser-unit acceleration.',
   'The state and controls match prior audited replays in recorded fields; unobserved state is not proven identical.',
   'Horizontal drag, collisions, field scale and full timing remain separate.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-vertical-full'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-ball-integration'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK:',sum(x['airborne_steps'] for x in r['directions'].values()),'airborne vertical steps')
if __name__=='__main__':main()
