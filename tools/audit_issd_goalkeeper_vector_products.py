"""Verify goalkeeper release fixed-point products against ROM and CPU hooks."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import span

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def words(n):
 n &= 0xffffffff
 return [n>>16,n&0xffff]

def audit(root,reference,rom_path,state):
 original=rom_path.read_bytes();head=len(original)%0x8000
 if head not in (0,512) or hashlib.md5(original[head:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 rom=original[head:];cases={}
 for name,direction,frame,angle,magnitude in [('Side',0,4472,0,88),('Up',7,4522,56,96),('Down',1,4522,4,96)]:
  action=root/name/'B';neutral=root/name/'NEUTRAL'
  for button,folder in (('B',action),('NEUTRAL',neutral)):
   if (folder/'trial.jsonl').read_bytes()!=(reference/name/button/'trial.jsonl').read_bytes():raise ValueError('Reference trial mismatch')
  events=read(action/'keeper-transfers.jsonl');controls=read(neutral/'keeper-transfers.jsonl')
  if not all(any(x.get('type')=='session_end' for x in rows) for rows in (events,controls)):raise ValueError('Incomplete trace')
  names=('839E32','839E92','839EC3','83953F')
  selected=[r for r in events if r.get('type')=='ball_vector_hook' and r['frame']==frame and r['address'] in names]
  if [x['address'] for x in selected]!=list(names):raise ValueError('Missing or unordered callbacks')
  if any(r.get('type')=='ball_vector_hook' and r['frame']==frame and r['address'] in names for r in controls):raise ValueError('Unexpected neutral callback')
  entry,product,corrected,stored=selected
  if (entry['a'],entry['y'],entry['ball_type'],entry['global_ac'],entry['global_ae'])!=(angle,magnitude,10,0,0):raise ValueError('Unexpected vector inputs')
  if span(rom,0x819632+direction,1)[0]!=angle:raise ValueError('Angle table mismatch')
  raw=span(rom,0x81a5d7+(angle&31)*4,4)
  coefficients=[int.from_bytes(raw[i:i+2],'little',signed=True) for i in (0,2)]
  products=[c*magnitude for c in coefficients]
  expected_signed=[products[0]*(-1 if ((angle+16)&63)>=32 else 1),products[1]*(-1 if angle>=32 else 1)]
  expected_products=[words(x) for x in products];expected_velocity=[words(x) for x in expected_signed]
  product_words=[[product['scratch00'],product['scratch02']],[product['scratch04'],product['scratch06']]]
  result_words=[[corrected['scratch00'],corrected['scratch02']],[corrected['scratch04'],corrected['scratch06']]]
  ball_words=[[stored['ball_vx'],stored['vx_fraction']],[stored['ball_vy'],stored['vy_fraction']]]
  if product_words!=expected_products or result_words!=expected_velocity or ball_words!=expected_velocity:raise ValueError('ROM multiplication, sign or store mismatch')
  cases[str(direction)]={'angle':angle,'magnitude':magnitude,'coefficient_address':f'81:{0xa5d7+(angle&31)*4:04X}',
   'coefficient_bytes':raw.hex(),'coefficients_signed':coefficients,'products_signed_32':expected_signed,
   'velocity_words':expected_velocity,'events':selected,'action_trace_sha256':sha(action/'keeper-transfers.jsonl'),
   'neutral_trace_sha256':sha(neutral/'keeper-transfers.jsonl'),'action_trial_sha256':sha(action/'trial.jsonl'),
   'neutral_trial_sha256':sha(neutral/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-vector-products-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'state_sha256':sha(state),'directions':cases,
  'limitations':['Three directions, one goalkeeper and one saved state; other angles and alternate paths require validation.',
    'Hooks observe instruction boundaries; only explicitly recorded words are compared.',
    'Fixed-point velocity units are native, not calibrated browser-world units.',
    'Later ball movement, collisions and release presentation require separate validation.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-vector-products'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-vector-hooks'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: three fixed-point vectors match Mode 7 and ball stores')
if __name__=='__main__':main()
