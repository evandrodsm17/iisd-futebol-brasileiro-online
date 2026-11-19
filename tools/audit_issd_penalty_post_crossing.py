"""Audit the post-crossing stationary horizontal state against captured goals."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
rom_path=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc')
rom=rom_path.read_bytes()
expected=bytes.fromhex('ad aa 14 89 00 08 d0 06 a5 10 05 2b d0 0b a9 30 8e 85 38 a9 8c 00 85 3a 6b ad aa 14 89 20 00 f0 08 64 28 64 29 64 32 64 33 a9 25 8e 85 38 a9 8c 00 85 3a 6b')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x60df1:0x60df1+len(expected)]!=expected:raise ValueError('Unexpected USA ROM or branch code')
root=Path('analysis/movement-progression-probe');captures=[]
for name in ('penalty-projection-Left-v3','penalty-projection-Right-v3','world-penalty-shot-vector'):
 raw=(root/name/'mode-hooks.jsonl').read_bytes();events=[json.loads(line) for line in raw.splitlines()]
 if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 samples=[]
 for crossing in (e for e in events if e.get('site')=='penalty_crossing_resolved'):
  frame=crossing['frame'];same=lambda e:all(e.get(k)==crossing[k] for k in ('d','side','round'))
  goals=[e for e in events if e.get('site')=='penalty_goal_branch' and e.get('frame')==frame and same(e)]
  if not goals:continue
  before=[e for e in events if e.get('site')=='penalty_shot_step' and e.get('frame')==frame and same(e)]
  after=[e for e in events if e.get('site')=='penalty_shot_step' and e.get('frame')==frame+1 and same(e)]
  if len(goals)!=1 or len(before)!=1 or len(after)!=1:raise ValueError('Ambiguous goal movement')
  b,a=before[0],after[0]
  if a['flags']&0x20==0 or a['dx'] or a['dx_ext'] or a['dy'] or a['dy_ext']:raise ValueError('Unexpected horizontal goal state')
  if any(a[p]!=(b[p]+b[v])&0xffff for p,v in (('px','dx'),('py','dy'),('pz','dz'))):raise ValueError('Unexpected movement')
  vz=(b['dz']|(b['dz_ext']<<16))+32;vz&=0xffffff
  if vz!=(a['dz']|(a['dz_ext']<<16)) or not(crossing['height']|(vz&0xffff)):raise ValueError('Unexpected vertical goal state')
  samples.append({'frame':frame,'side':crossing['side'],'round':crossing['round'],
   'crossing_flags':crossing['shot_flags'],'next_flags':a['flags'],'height':crossing['height'],'vertical_velocity':vz,
   'horizontal_before':[b['dx']|(b['dx_ext']<<16),b['dy']|(b['dy_ext']<<16)],'horizontal_after':[0,0]})
 captures.append({'name':name,'hooks_sha256':hashlib.sha256(raw).hexdigest(),'samples':samples})
if [len(c['samples']) for c in captures]!=[3,4,6]:raise ValueError('Unexpected sample coverage')
result={'schema':'issd-penalty-post-crossing/v1','rom_offset':'0x60df1','captures':captures,
 'limits':['Synthetic captures include repeated scenarios and are not independent trials.',
           '8C:8DF1 itself was not instrumented; the branch is established by ROM bytes and consistent next-frame state.',
           'The goal branch sets the relevant flag; other routines may modify flags or state between hooks.',
           'The code also has non-goal and deferred paths; those are not generalized from these 13 samples.',
           'ROM and raw captures remain local.']}
Path('docs/issd-penalty-post-crossing.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print('OK: 13 captured goals match post-crossing horizontal stop')
