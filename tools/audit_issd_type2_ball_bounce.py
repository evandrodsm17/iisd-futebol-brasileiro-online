"""Audit one observed native ball-type-2 bounce after a goalkeeper replay."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def val(r,k):return (r[k]<<16)|r[k+'_frac']
def audit(action,neutral,rom_path,state):
 raw=rom_path.read_bytes();head=len(raw)%0x8000
 if head not in (0,512) or hashlib.md5(raw[head:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 for off,code in [(0x1895d,'5636763460'),(0x18883,'38a90000f5349534a90000f5369536'),(0x189af,'ad56044a8d56044a186d56048d56'),(0x18fdd,'4e28046e2604ad28048500ad260485024e28046e2604186d2604'),(0x19019,'4e24046e2204ad24048500ad220485024e24046e2204186d2204')]:
  b=bytes.fromhex(code)
  if raw[head+off:head+off+len(b)]!=b:raise ValueError(f'Unexpected code at {off:x}')
 if raw[head+0xa877:head+0xa879]!=b'\0\0':raise ValueError('Unexpected ball type table')
 a=read(action/'trial.jsonl');n=read(neutral/'trial.jsonl');ar={x['step']:x for x in a if 'step' in x};nr={x['step']:x for x in n if 'step' in x}
 if set(ar)!=set(range(1,401)) or set(nr)!=set(ar) or any(ar[t]!=nr[t] for t in range(1,70)):raise ValueError('Incomplete or different baseline')
 if any(ar[t]['held_p1']!=0x8000 or nr[t]['held_p1']!=0 or ar[t]['selected']!=0x500 for t in range(70,76)):raise ValueError('Button mismatch')
 events=read(action/'keeper-transfers.jsonl');control=read(neutral/'keeper-transfers.jsonl')
 if not all(any(x.get('type')=='session_end' for x in rows) for rows in (events,control)):raise ValueError('Incomplete hook traces')
 names=['83882A','838941','83895D','838866','838883','83898D','8389AF','8388BB']
 found=[r for r in events if r.get('type')=='bounce_hook' and r['frame']==4673 and r['address'] in names]
 if [r['address'] for r in found]!=names or any(r['ball_type']!=2 for r in found):raise ValueError('Bounce path differs')
 if any(r.get('type')=='bounce_hook' and r['frame']==4673 and r['address']=='838883' for r in control):raise ValueError('Bounce also occurred in neutral')
 impact,half_entry,_,half_done,invert,negated,branch,done=found
 if (impact['weather'],impact['flags'],impact['parameter'])!=(1,0,11):raise ValueError('Bounce context differs')
 v=val(half_entry,'vz');half=v>>1
 if v!=0x18000 or val(half_done,'vz')!=half or val(invert,'vz')!=half or val(negated,'vz')!=(-half)&0xffffffff:raise ValueError('Vertical bounce mismatch')
 def three_quarters(v):return (v>>1)+(v>>2)
 for k in ('vx','vy'):
  v=val(branch,k)
  if v&0x80000000 or val(done,k)!=three_quarters(v):raise ValueError('Horizontal reduction mismatch')
 if (done['z'],done['z_frac'],done['parameter'],done['flags'])!=(0,0,7,1):raise ValueError('Unexpected final bounce state')
 return {'schema':'issd-ball-type2-bounce-audit/v1','rom_sha256':hashlib.sha256(raw[head:]).hexdigest(),'state_sha256':sha(state),
  'action_trial_sha256':sha(action/'trial.jsonl'),'neutral_trial_sha256':sha(neutral/'trial.jsonl'),
  'action_trace_sha256':sha(action/'keeper-transfers.jsonl'),'neutral_trace_sha256':sha(neutral/'keeper-transfers.jsonl'),
  'pre_input_samples_match':69,'frame':4673,'ball_type':2,'events':found,
  'limitations':['The ball changed to type 2 after the goalkeeper release; this is not validated as an immediate type-10 throw bounce.',
   'Only one impact, weather and branch; negative horizontal values, other speeds and weather are unverified.',
   'Inputs and sampled state match before action, but other hidden state is not proven identical.',
   'Native 16.16 units are not calibrated for browser-world physics.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',type=Path);p.add_argument('neutral',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.action,a.neutral,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: observed type-2 bounce and horizontal reduction')
if __name__=='__main__':main()
