"""Audit deterministic penalty direction replays from one local savestate."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
root=Path('analysis/movement-progression-probe');seed=root/'penalty-replay-seed';state=seed/'penalty-seed.State'
state_hash=hashlib.sha256(state.read_bytes()).hexdigest()
driver_path,=seed.glob('issd-auto-probe-*.jsonl');seed_raw=driver_path.read_bytes();seed_events=[json.loads(l) for l in seed_raw.splitlines()]
if seed_events[-1].get('type')!='session_end' or len([e for e in seed_events if e.get('type')=='penalty_state_saved'])!=1 or not any(e.get('type')=='penalty_decoder_observed' for e in seed_events):raise ValueError('Invalid seed capture')
saved=next(e for e in seed_events if e.get('type')=='penalty_state_saved')
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x63d7c:0x63d7f]!=bytes([0x28,0,0x50]) or rom[0xddd8:0xdddd]!=bytes([1,9,8,10,2]):raise ValueError('Unexpected ROM')
inputs={'neutral':0,'Left':0x200,'Right':0x100,'Up':0x800,'Down':0x400,'UpLeft':0xa00,'UpRight':0x900,'DownLeft':0x600,'DownRight':0x500}
runs=[]
for direction,controller in [(d,'p1') for d in inputs]+[('Left','p2')]:
 folder=root/f'penalty-replay-{direction.lower()}-{controller}'
 dr=(folder/'replay.jsonl').read_bytes();driver=[json.loads(l) for l in dr.splitlines()]
 hr=(folder/'mode-hooks.jsonl').read_bytes();hooks=[json.loads(l) for l in hr.splitlines()]
 if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in hooks):raise ValueError('Incomplete replay')
 info=driver[0]
 if (info['direction'],info['controller'],info['start_frame'],info['action_pulses'])!=(direction,controller,saved['frame'],'both'):raise ValueError('Unexpected replay setup')
 if len([e for e in driver if e.get('type')=='sample'])!=info['steps']:raise ValueError('Missing sampled frames')
 shots=[e for e in hooks if e.get('site')=='penalty_shot_final' and e['side']==0 and e['round']==1]
 if len(shots)!=1:raise ValueError('Missing matched shot')
 shot=shots[0];frames=[e for e in driver if e.get('type')=='sample' and e['frame']==shot['frame']]
 if len(frames)!=1:raise ValueError('No input sample at shot frame')
 sample=frames[0];desired=sample['held_p1'] if controller=='p1' else sample['held_p2'];other=sample['held_p2'] if controller=='p1' else sample['held_p1']
 if (desired&0xf00)!=inputs[direction] or (other&0xf00)!=0 or sample['action']:raise ValueError('Unexpected held inputs at shot frame')
 vectors=[e for e in hooks if e.get('site')=='penalty_shot_vector' and e['frame']==shot['frame'] and all(e[k]==shot[k] for k in ('d','side','round'))]
 if len(vectors)!=1:raise ValueError('Ambiguous shot vector')
 v=vectors[0];code=(shot['input_word']>>8)&11;codes=list(rom[0xddd8:0xdddd]);base=codes.index(code) if code in codes else 2
 offset=rom[0x63d7c+v['variant']]+2*base
 if v['x']!=offset or v['index']!=base+(0 if v['flags']&0x10 else 5):raise ValueError('Direction index mismatch')
 def signed(at):return int.from_bytes(rom[at:at+2],'little',signed=True)
 vector=[signed(0x63d95+offset),signed(0x63d8b+offset),signed((0x63da9 if v['flags']&0x10 else 0x63d9f)+offset)]
 for k,word in zip(('dx','dy','dz'),vector):
  if v[k]|v[k+'_ext']<<16!=word&0xffffff:raise ValueError('Vector mismatch')
 runs.append({'direction':direction,'controller':controller,'driver_sha256':hashlib.sha256(dr).hexdigest(),
  'hooks_sha256':hashlib.sha256(hr).hexdigest(),'shot_frame':shot['frame'],'side':shot['side'],'round':shot['round'],
  'held_p1':sample['held_p1'],'held_p2':sample['held_p2'],'input_word':shot['input_word'],
  'index':v['index'],'variant':v['variant'],'flags':v['flags'],'vector':vector})
if len({r['shot_frame'] for r in runs})!=1:raise ValueError('Shots not aligned')
output={'schema':'issd-penalty-direction-replay/v1','seed_sha256':state_hash,'seed_driver_sha256':hashlib.sha256(seed_raw).hexdigest(),
 'seed_frame':saved['frame'],'runs':runs,
 'limits':['One synthetic shootout and a single saved state; directions share the same earlier match history.',
           'The controls are sampled after frame advance; the native shot hook runs within that frame.',
           'A is periodically pulsed on both controls, though it is not held at the compared shot frame.',
           'This establishes one role and shot context only, not goalkeeper direction, visual trajectory or universal controls.',
           'Savestate, ROM, screenshots and raw traces remain local.']}
Path('docs/issd-penalty-direction-replay.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print('OK: 8 directions and neutral on P1, plus Left on P2, from one captured state')
