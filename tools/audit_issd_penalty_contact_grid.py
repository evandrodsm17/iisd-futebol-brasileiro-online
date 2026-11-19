"""Audit a 3x3 synthetic shootout/keeper contact matrix against native hitboxes."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from audit_issd_penalty_hitboxes import collision
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x62375:0x62375+8]!=bytes.fromhex('b9 00 00 8d 00 00 c8 c8'):raise ValueError('Unexpected ROM')
root=Path('analysis/movement-progression-probe');cases=[]
inputs={'left':0x200,'neutral':0,'right':0x100}
for shooter in inputs:
 for keeper in inputs:
  folder=root/f'penalty-contact-grid-{shooter}-{keeper}';dr=(folder/'replay.jsonl').read_bytes();hr=(folder/'mode-hooks.jsonl').read_bytes()
  driver=[json.loads(l) for l in dr.splitlines()];hooks=[json.loads(l) for l in hr.splitlines()]
  if driver[0].get('type')!='session_start' or driver[-1].get('type')!='session_end' or hooks[0].get('site')!='session_start' or hooks[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in hooks):raise ValueError('Incomplete replay')
  setup=driver[0]
  if (setup['controller'],setup['direction'].lower(),setup['players_before'],setup['players_after'],setup['synthetic_players'],setup['action_pulses'])!=('p2',keeper,0,4,True,'p1-periodic-p2-window'):raise ValueError('Unexpected setup')
  windows=[e for e in driver if e.get('type')=='direction_windows']
  if len(windows)!=1 or (windows[0]['p2_or_selected_start'],windows[0]['p1_direction'].lower(),windows[0]['p1_start'])!=(1420,shooter,1420):raise ValueError('Direction windows differ')
  actions=[e for e in driver if e.get('type')=='synthetic_p2_action']
  if [e['start_step'] for e in actions]!=[955,1455]:raise ValueError('Unexpected action windows')
  def events(site):return [e for e in hooks if e.get('site')==site and e.get('side')==0 and e.get('round')==1]
  def single(site):
   es=events(site)
   if len(es)!=1:raise ValueError(f'Ambiguous {site}')
   return es[0]
  shot=single('penalty_shot_final');decode=single('penalty_direction_decode_start');cross=single('penalty_crossing_resolved')
  if shot['input_word']!=inputs[shooter] or decode['input_word']!=inputs[keeper]|0x80:raise ValueError('Unexpected native input')
  sample=[e for e in driver if e.get('type')=='sample' and e['frame']==decode['frame']+1]
  if len(sample)!=1 or sample[0]['held_p1']!=inputs[shooter] or sample[0]['held_p2']!=inputs[keeper]|0x80 or not sample[0]['action_p2']:raise ValueError('Input sample mismatch')
  hits=events('collision_hit');selected=events('penalty_collision_selected');goals=events('penalty_goal_branch')
  if len(hits)==len(selected)==1 and not goals:
   hit,sel=hits[0],selected[0];action=single('penalty_contact_action');deferred=single('penalty_deferred_finalize')
   if not collision(rom,hit) or hit['frame']!=sel['frame'] or hit['dp']!=sel['d'] or hit['other']!=sel['linked_object'] or action['linked_object']!=sel['d'] or not(action['frame']>sel['frame'] and deferred['frame']==cross['frame']):raise ValueError('Invalid contact chain')
   if [cross['penalty_home'],cross['penalty_away']]!=[sel['penalty_home'],sel['penalty_away']]:raise ValueError('Unexpected contact score')
   geometry={'x':hit['x'],'y':hit['y'],'z':hit['z'],'otherX':hit['other_x'],'otherY':hit['other_y'],'otherZ':hit['other_z'],'objectFlags':hit['object_flags'],'offset':hit['offset']}
   observation={'outcome':'contact_deferred','contact_frame':hit['frame'],'selector':hit['selector'],'geometry':geometry,'flags':sel['shot_flags'],'shot_index':shot['direction'],'before_score':[sel['penalty_home'],sel['penalty_away']]}
  elif not hits and not selected and len(goals)==1:
   goal=goals[0]
   if goal['frame']!=cross['frame'] or [cross['penalty_home'],cross['penalty_away']]!=[goal['penalty_home']+1,goal['penalty_away']]:raise ValueError('Unexpected goal score')
   observation={'outcome':'goal_branch','before_score':[goal['penalty_home'],goal['penalty_away']]}
  else:raise ValueError('Unexpected route')
  cases.append({'shooter':shooter,'keeper':keeper,'driver_sha256':hashlib.sha256(dr).hexdigest(),'hooks_sha256':hashlib.sha256(hr).hexdigest(),
    'shot_frame':shot['frame'],'input_word':shot['input_word'],'keeper_input_word':decode['input_word'],'resolution_frame':cross['frame'],
    'after_score':[cross['penalty_home'],cross['penalty_away']],**observation})
if sum(c['outcome']=='contact_deferred' for c in cases)!=3:raise ValueError('Unexpected contact coverage')
output={'schema':'issd-penalty-contact-grid/v1','cases':cases,
 'limits':['Nine replays from one synthetic state with player count changed from 0 to 4.',
           'The compared P2 buttons were sampled one frame after the native direction hook.',
           'Three selected contacts reached deferred resolution with no score increment; save type is not established.',
           'The captured outcome is not a rule for arbitrary trajectories, teams, timing, positions or goalkeeper AI.',
           'Native hitbox tables, ROM, savestate, raw traces and images remain local.']}
Path('docs/issd-penalty-contact-grid.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-contact-grid.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 9 synthetic cases, including 3 native hitbox contacts')
