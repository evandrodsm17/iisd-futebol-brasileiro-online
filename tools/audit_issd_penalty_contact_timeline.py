"""Audit every recorded goalkeeper-ball collision check for six synthetic replays."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from audit_issd_penalty_hitboxes import collision
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x62375:0x62375+8]!=bytes.fromhex('b9 00 00 8d 00 00 c8 c8'):raise ValueError('Unexpected ROM')
root=Path('analysis/movement-progression-probe');cases=[]
for shooter,keeper in [('left','left'),('neutral','neutral'),('right','right'),('left','neutral'),('neutral','left'),('right','neutral')]:
 folder=root/f'penalty-contact-sequence-{shooter}-{keeper}';dr=(folder/'replay.jsonl').read_bytes();hr=(folder/'mode-hooks.jsonl').read_bytes()
 driver=[json.loads(l) for l in dr.splitlines()];hooks=[json.loads(l) for l in hr.splitlines()]
 if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in hooks):raise ValueError('Incomplete replay')
 info=driver[0]
 if (info['controller'],info['direction'].lower(),info['players_before'],info['players_after'],info['synthetic_players'])!=('p2',keeper,0,4,True):raise ValueError('Unexpected setup')
 if len([e for e in hooks if e.get('site')=='collision_capture_all'])!=1:raise ValueError('Missing full collision capture marker')
 settings=[e for e in driver if e.get('type')=='direction_windows']
 if len(settings)!=1 or (settings[0]['p2_or_selected_start'],settings[0]['p1_direction'].lower(),settings[0]['p1_start'])!=(1420,shooter,1420):raise ValueError('Unexpected direction windows')
 rawchecks=[e for e in hooks if e.get('side')==0 and e.get('round')==1 and e.get('site') in ('collision_hit','collision_miss')]
 checks=[]
 for e in rawchecks:
  if e['dp']!=0x500 or e['other']!=0x700 or collision(rom,e)!=(e['site']=='collision_hit'):raise ValueError('Collision mismatch')
  geometry={'x':e['x'],'y':e['y'],'z':e['z'],'otherX':e['other_x'],'otherY':e['other_y'],'otherZ':e['other_z'],'objectFlags':e['object_flags'],'offset':e['offset']}
  checks.append({'frame':e['frame'],'selector':e['selector'],'geometry':geometry,'hit':e['site']=='collision_hit'})
 if not checks or sum(c['hit'] for c in checks)!=(1 if shooter==keeper else 0):raise ValueError('Unexpected result')
 if any(a['frame']>=b['frame'] for a,b in zip(checks,checks[1:])):raise ValueError('Collision sequence is not ordered')
 launches=[e for e in hooks if e.get('site')=='penalty_shot_vector' and e.get('side')==0 and e.get('round')==1 and e.get('d')==0x700]
 if len(launches)!=1:raise ValueError('Ambiguous launch')
 launch=launches[0]
 initial={'x':launch['px'],'y':launch['py'],'z':launch['pz']}
 initial.update({name:launch[key]|launch[key+'_ext']<<16 for name,key in (('vx','dx'),('vy','dy'),('vz','dz'))})
 state=initial.copy();by_frame={c['frame']:c for c in checks}
 for frame in range(launch['frame']+1,checks[-1]['frame']+2):
  steps=[e for e in hooks if e.get('site')=='penalty_shot_step' and e.get('d')==0x700 and e.get('side')==0 and e.get('round')==1 and e.get('frame')==frame]
  if len(steps)!=1:raise ValueError('Ambiguous motion sample')
  step=steps[0]
  for pos,key in (('x','px'),('y','py'),('z','pz')):
   if state[pos]&0xffff!=step[key]:raise ValueError('Continuous position mismatch')
  for vel,key in (('vx','dx'),('vy','dy'),('vz','dz')):
   if state[vel]!=(step[key]|step[key+'_ext']<<16):raise ValueError('Continuous velocity mismatch')
  if frame>launch['frame']+1 and frame-1 in by_frame:
   check=by_frame[frame-1];observed=check['geometry']
   if any(((state[pos]>>8)&255)!=observed[key] for pos,key in (('x','otherX'),('y','otherY'),('z','otherZ'))):raise ValueError('Collision ball position mismatch')
   check['ball_low']=[step['px'],step['py'],step['pz']]
  if frame<=checks[-1]['frame']:
   for pos,vel in (('x','vx'),('y','vy'),('z','vz')):state[pos]=(state[pos]+state[vel])&0xffffff
   state['vz']=(state['vz']+32)&0xffffff
 cases.append({'shooter':shooter,'keeper':keeper,'driver_sha256':hashlib.sha256(dr).hexdigest(),'hooks_sha256':hashlib.sha256(hr).hexdigest(),
               'launch_frame':launch['frame'],'initial':initial,'gravity':32,'checks':checks})
if sum(len(c['checks']) for c in cases)!=81:raise ValueError('Unexpected check count')
output={'schema':'issd-penalty-contact-timeline/v1','cases':cases,
 'limits':['Six replays from one synthetic saved state with player setting changed from 0 to 4.',
           'Collision calls and ball movement were logged; missing collision calls are not interpreted as misses.',
           'The comparison uses native bytes and selectors, not browser-screen coordinates.',
           'A positive hit alone does not determine the response, final result or type of save.',
           'ROM, local extracted hitbox tables, saved state and raw logs remain local.']}
Path('docs/issd-penalty-contact-timeline.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-contact-timeline.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 81 native collision checks in six replay sequences')
