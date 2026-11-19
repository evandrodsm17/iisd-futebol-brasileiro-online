"""Contrast phase words in a menu with actual native penalty execution."""
import hashlib,json
from pathlib import Path
root=Path('analysis/movement-progression-probe')
def load(name):
 folder=root/name;drivers=list(folder.glob('issd-auto-probe-*.jsonl'))
 if len(drivers)!=1:raise ValueError('Ambiguous driver')
 raw=drivers[0].read_bytes();events=[json.loads(l) for l in raw.splitlines()]
 hook=(folder/'mode-hooks.jsonl').read_bytes();hooks=[json.loads(l) for l in hook.splitlines()]
 if events[0].get('type')!='session_start' or events[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 return raw,events,hook,hooks
def scene(e):return (e.get('mode1'),e.get('mode2'),e.get('phase'))==(6,12,9)
neg_raw,negative,neg_hook,neg_events=load('penalty-shot-gate-negative')
configs=[e for e in negative if e.get('type')=='penalty_direction_config']
if len(configs)!=1 or configs[0]['direction']!='Up' or configs[0]['controllers']!='p1':raise ValueError('Unexpected negative setup')
matching=[e for e in negative if scene(e)]
if not matching or any(e.get('type')=='penalty_decoder_observed' for e in negative) or any(e.get('site')=='penalty_shot_decode_start' for e in neg_events) or any('+Up' in e.get('input','') for e in matching):raise ValueError('Unexpected negative gate')
pos_raw,positive,pos_hook,pos_events=load('world-penalty-shot-vector')
decodes=[e for e in pos_events if e.get('site')=='penalty_shot_decode_start']
if not decodes:raise ValueError('No positive penalty decoder')
first=decodes[0];later=[e for e in positive if scene(e) and first['frame']<e.get('frame',0)<=first['frame']+40]
if not later or not all('+Right' in e.get('input','') for e in later):raise ValueError('Positive trace did not hold direction after decoder')
result={'schema':'issd-penalty-scene-gate/v1','negative':{'driver_sha256':hashlib.sha256(neg_raw).hexdigest(),'hooks_sha256':hashlib.sha256(neg_hook).hexdigest(),
  'phase_samples':len(matching),'first_step':matching[0]['step'],'last_step':matching[-1]['step'],'decoder_events':0,'direction_samples':0},
 'historical_positive':{'driver_sha256':hashlib.sha256(pos_raw).hexdigest(),'hooks_sha256':hashlib.sha256(pos_hook).hexdigest(),
  'first_decoder_frame':first['frame'],'later_phase_samples':len(later),'first_later_sample_frame':later[0]['frame']},
 'limits':['Negative synthetic run reached a controller menu, not a penalty scene.',
           'Positive historical capture predates the gate and uses synthetic score and clock.',
           'Samples are every ten frames and do not prove continuous phase or directly test the new positive gate.',
           'The shot decoder can arm only subsequent frames and may miss the first shot.',
           'ROM, raw logs and screenshots stay local.']}
Path('docs/issd-penalty-scene-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(f"OK: {len(matching)} misleading menu samples rejected; historical penalty decoder observed")
