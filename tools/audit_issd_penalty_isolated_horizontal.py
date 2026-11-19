"""Compare isolated horizontal commands to captured shot words and ROM vectors."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
root=Path('analysis/movement-progression-probe')
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x63d7c:0x63d7f]!=bytes([0x28,0,0x50]) or rom[0xddd8:0xdddd]!=bytes([1,9,8,10,2]):raise ValueError('Unexpected ROM')
results=[]
for direction in ('Left','Right'):
 for controller in ('p1','p2'):
  folder=root/f'penalty-shot-input-{direction.lower()}-{controller}-v7';drivers=list(folder.glob('issd-auto-probe-*.jsonl'))
  if len(drivers)!=1:raise ValueError('Ambiguous capture')
  driver_raw=drivers[0].read_bytes();driver=[json.loads(l) for l in driver_raw.splitlines()]
  hooks_raw=(folder/'mode-hooks.jsonl').read_bytes();hooks=[json.loads(l) for l in hooks_raw.splitlines()]
  if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
  configs=[e for e in driver if e.get('type')=='penalty_direction_config']
  if len(configs)!=1 or configs[0]['direction']!=direction or configs[0]['controllers']!=controller:raise ValueError('Unexpected setup')
  if any(not any(e.get('type')==name for e in driver) for name in ('synthetic_score','synthetic_clock','synthetic_unstick_config')):raise ValueError('Synthetic preparation missing')
  armed=[e for e in driver if e.get('type')=='penalty_decoder_observed']
  if not armed:raise ValueError('Decoder gate was not armed')
  samples=[e for e in driver if e.get('mode1')==6 and e.get('mode2')==12 and e.get('phase')==9 and e.get('frame',0)>armed[0]['frame'] and ('+'+direction in e.get('input','') or direction in e.get('input_p2',''))]
  if not samples:raise ValueError('No direction samples')
  if any(('+'+direction in e.get('input',''))!=(controller=='p1') or (direction in e.get('input_p2',''))!=(controller=='p2') for e in samples):raise ValueError('Input not isolated')
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
  if len(shots)<3:raise ValueError('Need three observed shots')
  results.append({'direction':direction,'controller':controller,'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),
                  'hooks_sha256':hashlib.sha256(hooks_raw).hexdigest(),'gate_frame':armed[0]['frame'],'input_samples':len(samples),'shots':shots})
output={'schema':'issd-penalty-isolated-horizontal/v1','runs':results,
 'limits':['Synthetic score, accelerated clock, menu confirmations and periodic A during active play.',
           'First shot precedes the decoder gate; isolated direction is applied only afterward.',
           'Button A may still be sent to both controls during scene progression.',
           'Inputs were sampled periodically; the exact held buttons at a given decoder call are not directly captured.',
           'Controller roles, screen mapping and behavior in other contexts are not established.',
           'ROM, raw logs and screenshots stay local.']}
Path('docs/issd-penalty-isolated-horizontal.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print('OK: 4 isolated horizontal controller captures, ROM vectors verified')
