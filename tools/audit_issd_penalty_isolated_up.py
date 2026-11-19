"""Audit isolated Up controller inputs in the native penalty scene."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
root=Path('analysis/movement-progression-probe')
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x63d7c:0x63d7f]!=bytes([0x28,0,0x50]) or rom[0xddd8:0xdddd]!=bytes([1,9,8,10,2]):raise ValueError('Unexpected ROM')
results=[]
for controller in ('p1','p2'):
 folder=root/f'penalty-shot-input-up-{controller}-v6';drivers=list(folder.glob('issd-auto-probe-*.jsonl'))
 if len(drivers)!=1:raise ValueError('Ambiguous capture')
 driver_raw=drivers[0].read_bytes();driver=[json.loads(l) for l in driver_raw.splitlines()]
 hooks_raw=(folder/'mode-hooks.jsonl').read_bytes();hooks=[json.loads(l) for l in hooks_raw.splitlines()]
 if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 config=[e for e in driver if e.get('type')=='penalty_direction_config']
 if len(config)!=1 or config[0]['direction']!='Up' or config[0]['controllers']!=controller:raise ValueError('Unexpected direction or controller')
 if not any(e.get('type')=='synthetic_unstick_config' for e in driver):raise ValueError('Unstick preparation not recorded')
 if not any(e.get('type')=='synthetic_score' for e in driver) or not any(e.get('type')=='synthetic_clock' for e in driver):raise ValueError('Synthetic preparation not recorded')
 armed=[e for e in driver if e.get('type')=='penalty_decoder_observed']
 if not armed:raise ValueError('Decoder gate was not armed')
 samples=[e for e in driver if e.get('mode1')==6 and e.get('mode2')==12 and e.get('phase')==9 and e.get('frame',0)>armed[0]['frame'] and ('+Up' in e.get('input','') or 'Up' in e.get('input_p2',''))]
 if not samples:raise ValueError('No direction samples after gate')
 if any(('+Up' in e.get('input',''))!=(controller=='p1') or ('Up' in e.get('input_p2',''))!=(controller=='p2') for e in samples):raise ValueError('Input not isolated')
 shots=[]
 for launch in (e for e in hooks if e.get('site')=='penalty_shot_final'):
  vectors=[e for e in hooks if e.get('site')=='penalty_shot_vector' and e.get('frame')==launch['frame'] and all(e[k]==launch[k] for k in ('d','side','round'))]
  if len(vectors)!=1:raise ValueError('Ambiguous vector')
  v=vectors[0];code=(launch['input_word']>>8)&11;codes=list(rom[0xddd8:0xdddd]);base=codes.index(code) if code in codes else 2
  offset=rom[0x63d7c+v['variant']]+2*base
  if v['x']!=offset or v['index']!=base+(0 if v['flags']&0x10 else 5):raise ValueError('Index mismatch')
  def signed(at):return int.from_bytes(rom[at:at+2],'little',signed=True)
  vector=[signed(0x63d95+offset),signed(0x63d8b+offset),signed((0x63da9 if v['flags']&0x10 else 0x63d9f)+offset)]
  for key,value in zip(('dx','dy','dz'),vector):
   if v[key]|(v[key+'_ext']<<16)!=value&0xffffff:raise ValueError('Vector mismatch')
  shots.append({'frame':launch['frame'],'side':launch['side'],'round':launch['round'],'input_word':launch['input_word'],
                'index':v['index'],'variant':v['variant'],'flags':v['flags'],'vector':vector})
 if len(shots)<2:raise ValueError('Need at least two observed shots')
 results.append({'controller':controller,'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'hooks_sha256':hashlib.sha256(hooks_raw).hexdigest(),
                 'gate_frame':armed[0]['frame'],'input_samples':len(samples),'shots':shots})
output={'schema':'issd-penalty-isolated-up/v1','runs':results,
 'limits':['Synthetic scores, accelerated clocks, menu confirmations and periodic A during active play.',
           'The first shot precedes the decoder gate; the direction is applied only afterward.',
           'Button A may still be sent to both controllers for menu or scene progression.',
           'Held-direction samples are periodic and do not prove the exact state at each decoder call.',
           'The captures do not establish a universal player-role mapping or visual trajectory.',
           'ROM, screenshots and raw logs stay local.']}
Path('docs/issd-penalty-isolated-up.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print('OK: isolated Up controller captures with native shot vectors')
