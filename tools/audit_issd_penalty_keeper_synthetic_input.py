"""Compare synthetic two-player goalkeeper inputs and native selector events."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
expected=bytes.fromhex('64 20 64 30 64 33 20 2b 9e 8d 08 17 20 49 a2')
height=bytes.fromhex('ad 1a 14 89 80 00 f0 1b a9 08 00 04 30 ad 08 17 18 69 05 00 8d 08 17')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x620a3:0x620a3+len(expected)]!=expected or rom[0x620d5:0x620d5+len(height)]!=height:raise ValueError('Unexpected ROM code')
root=Path('analysis/movement-progression-probe');runs=[]
for direction,word in [('neutral',0x80),('left',0x280),('right',0x180)]:
 folder=root/f'penalty-keeper-second-action-{direction}';driver_raw=(folder/'replay.jsonl').read_bytes();hook_raw=(folder/'mode-hooks.jsonl').read_bytes()
 driver=[json.loads(l) for l in driver_raw.splitlines()];hooks=[json.loads(l) for l in hook_raw.splitlines()]
 if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in hooks):raise ValueError('Incomplete capture')
 setup=driver[0]
 if (setup['controller'],setup['direction'].lower(),setup['players_before'],setup['players_after'],setup['synthetic_players'],setup['action_pulses'])!=('p2',direction,0,4,True,'p1-periodic-p2-window'):raise ValueError('Unexpected synthetic setup')
 windows=[e for e in driver if e.get('type')=='synthetic_p2_action']
 if [e['start_step'] for e in windows]!=[955,1455] or any(e['duration']!=8 for e in windows):raise ValueError('Unexpected action windows')
 def one(site):
  found=[e for e in hooks if e.get('site')==site and e.get('side')==0 and e.get('round')==1]
  if len(found)!=1:raise ValueError(f'Ambiguous {site}')
  return found[0]
 shot=one('penalty_shot_final');start=one('penalty_direction_decode_start');end=one('penalty_direction_decode_end');before=one('penalty_cpu_before');after=one('penalty_cpu_after')
 if shot['input_word']!=0 or any(e['frame']!=start['frame'] for e in (end,before,after)) or any(e['input_word']!=word for e in (start,end,before,after)) or before['player_setting']!=4 or after['player_setting']!=4:raise ValueError('Mismatch in decoder context')
 sample=[e for e in driver if e.get('type')=='sample' and e['frame']==start['frame']+1]
 if len(sample)!=1 or sample[0]['held_p2']!=word or sample[0]['held_p1']!=0 or not sample[0]['action_p2']:raise ValueError('Controller sample mismatch')
 code=(word>>8)&11;table=[1,9,8,10,2];base=table.index(code) if code in table else 2
 if end['a']!=base or before['direction']!=base:raise ValueError('Decoder mismatch')
 expected_final=after['direction']+(5 if word&0x80 else 0)
 selectors=[e for e in hooks if e.get('site')=='penalty_selector_write' and e.get('side')==0 and e.get('round')==1 and start['frame']<=e['frame']<start['frame']+60]
 if not selectors or any(e['direction_word']!=expected_final for e in selectors):raise ValueError('Animation selector mismatch')
 runs.append({'direction':direction,'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'hooks_sha256':hashlib.sha256(hook_raw).hexdigest(),
  'shot_frame':shot['frame'],'decode_frame':start['frame'],'sample_frame':sample[0]['frame'],'held_p2':sample[0]['held_p2'],
  'input_word':word,'base':base,'after_cpu':after['direction'],'final_index':expected_final,
  'selectors':[{'frame':e['frame'],'value':e['value']} for e in selectors]})
output={'schema':'issd-penalty-keeper-synthetic-input/v1','rom_offsets':['0x620a3','0x620d5'],'runs':runs,
 'limits':['One saved state from a synthetic match; number-of-players RAM changed from 0 to 4 after loading.',
           'The override does not prove that all controller or roster state matches a naturally configured two-player game.',
           'P2 A was injected in two chosen windows; P1 continued receiving periodic A pulses.',
           'P2 was sampled one frame after the native decoder hook.',
           'Selectors are internal animation values, not independently verified graphical poses or save outcomes.',
           'ROM, saved state, screenshots and raw logs remain local.']}
Path('docs/issd-penalty-keeper-synthetic-input.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print('OK: synthetic P2 neutral, left and right inputs reach distinct native keeper indices')
