"""Audit penalty goalkeeper proxy initialization and movement against the ROM."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
expected=bytes.fromhex('20 73 9f a5 0c 85 12 a5 10 05 2b f0 1e a5 2b 18 69 38 00 85 2b e2 20 a5 2d 69 00 85 2d c2 20 a5 10 30 6a 64 10 64 2b 64 2c 80 62 a4 36 b9 30 00 89 02 00 d0 5b 9c 01 00 a5 10 d0 51 a9 3e 00 a6 28 e8 e0 00 00 30 06 ce 01 00 a9 d0 ff 8d 00 00 a5 28 18 6d 00 00 85 28 e2 20 a5 2a 6d 02 00 85 2a c2 20 9c 05 00 a9 38 00 a6 32 e8 e0 00 00 30 06 ce 05 00 a9 d0 ff 8d 04 00 a5 32 18 6d 04 00 85 32 e2 20 a5 34 6d 06 00 85 34 c2 20 20 56 a0 60')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x62125:0x62125+len(expected)]!=expected:raise ValueError('Unexpected keeper motion routine')
stop=bytes.fromhex('a5 2b 10 04 49 ff ff 1a c9 40 00 b0 15 a5 10 10 04 49 ff ff 1a c9 02 00 b0 08 64 2b 64 2c 64 10 64 0e a5 28 10 04 49 ff ff 1a c9 40 00 b0 08 a5 10 d0 19 64 28 64 29 a5 32 10 04 49 ff ff 1a c9 40 00 b0 08 a5 10 d0 04 64 32 64 33 60')
if rom[0x62056:0x62056+len(stop)]!=stop:raise ValueError('Unexpected stop routine')
MASK=0xffffff;fields=('x','y','z','vx','vy','vz')
def abs16(x):
 x&=0xffff
 return (-x)&0xffff if x&0x8000 else x
def advance(before,linked):
 result=before.copy()
 for p,v in (('x','vx'),('y','vy'),('z','vz')):result[p]=(result[p]+result[v])&MASK
 height=(result['z']>>8)&0xffff
 if height|(result['vz']&0xffff):
  result['vz']=(result['vz']+0x38)&MASK
  if not(height&0x8000):result['z']&=255;result['vz']=0
 else:
  if linked&2:return result,'ground_linked'
  for v,delta in [('vx',0x3e),('vy',0x38)]:
   neg=bool(((result[v]&0xffff)+1)&0x8000)
   result[v]=(result[v]+(delta if neg else -0x30))&MASK
 height=(result['z']>>8)&0xffff
 if abs16(result['vz'])<0x40 and abs16(height)<2:result['vz']=0;result['z']=0
 if abs16(result['vx'])<0x40 and result['z']>>8==0:result['vx']=0
 if abs16(result['vy'])<0x40 and result['z']>>8==0:result['vy']=0
 return result,'air_or_friction'
root=Path('analysis/movement-progression-probe');captures=[]
for direction in ['left','neutral','right']:
 folder=root/f'penalty-keeper-motion-{direction}-{direction}';hr=(folder/'mode-hooks.jsonl').read_bytes();dr=(folder/'replay.jsonl').read_bytes();hooks=[json.loads(l) for l in hr.splitlines()];driver=[json.loads(l) for l in dr.splitlines()]
 if hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end' or driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or not any(e.get('site')=='keeper_motion_capture' for e in hooks):raise ValueError('Incomplete capture')
 if not driver[0].get('synthetic_players') or driver[0]['players_after']!=4:raise ValueError('Missing synthetic setting')
 start=[e for e in hooks if e.get('site')=='keeper_init_end'];
 if len(start)!=1:raise ValueError('Ambiguous initial state')
 init=start[0];base=init['direction']-5
 if base not in range(5) or init['state_flags']&8==0:raise ValueError('Unexpected initial direction')
 def word(at):return int.from_bytes(rom[at:at+2],'little',signed=True)&MASK
 if (init['vx'],init['vy'],init['stored_jump'],init['vz'])!=(word(0x63e0d+base*2),word(0x63e03+base*2),word(0x63e21+base*2),0):raise ValueError('Initial vector mismatch')
 samples=[]
 for a in (e for e in hooks if e.get('site')=='keeper_move_start'):
  ending=[e for e in hooks if e.get('site')=='keeper_move_end' and e.get('frame')==a['frame'] and e.get('d')==a['d']]
  if len(ending)!=1:raise ValueError('Ambiguous movement pair')
  end=ending[0];before={k:a[k] for k in fields};actual={k:end[k] for k in fields};modeled,branch=advance(before,a['linked_flags'])
  if modeled!=actual:raise ValueError(f'Movement mismatch {direction} frame {a["frame"]}: {modeled} vs {actual}')
  samples.append({'frame':a['frame'],'linked_flags':a['linked_flags'],'state_flags':a['state_flags'],'stored_jump':a['stored_jump'],'before':before,'after':actual,'branch':branch})
 initial={k:init[k] for k in fields};previous=initial;impulses=[]
 for sample in samples:
  changes={k for k in fields if previous[k]!=sample['before'][k]}
  if changes:
   if changes!={'vz'} or previous['vz']!=0 or sample['before']['vz']!=init['stored_jump']:raise ValueError('Unexpected between-call state change')
   impulses.append({'frame':sample['frame'],'vz':sample['before']['vz']})
  previous=sample['after']
 if len(impulses)!=1:raise ValueError('Unexpected observed impulse count')
 captures.append({'direction':direction,'hooks_sha256':hashlib.sha256(hr).hexdigest(),'driver_sha256':hashlib.sha256(dr).hexdigest(),
  'initial':initial,'initial_index':init['direction'],'stored_jump':init['stored_jump'],'observed_impulses':impulses,'samples':samples})
if [len(c['samples']) for c in captures]!=[38,29,40]:raise ValueError('Unexpected movement coverage')
output={'schema':'issd-penalty-keeper-motion/v1','rom_offsets':['0x62125','0x62056','0x63e03','0x63e0d','0x63e21'],'captures':captures,
 'limits':['Three replays from one synthetic state with player count changed to 4.',
           'Impulse frames are observed state changes in these recordings, not a general scheduling rule.',
           'Linked-object flags and scheduling must be supplied by the caller.',
           'Initialization values represent only the action-flag branch for these three directions.',
           'Keeper proxy coordinates are native units and do not determine screen position or complete animation.',
           'ROM, local tables, saved state and raw traces remain local.']}
Path('docs/issd-penalty-keeper-motion.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-keeper-motion.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 107 goalkeeper motion calls match ROM')
