"""Audit lateral keeper animation flag writes and their observed correlation."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
expected=bytes.fromhex('a0 06 ee a9 e2 ed 20 8f a6 a0 c2 de 84 1e 20 2d 95 a9 00 20 04 30 a9 08 00 14 30 a9 d2 91 85 38 a9 8c 00 85 3a 6b')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x611ac:0x611ac+len(expected)]!=expected:raise ValueError('Unexpected lateral animation state')
landing=bytes.fromhex('20 a3 a6 a5 10 30 0f a9 02 20 14 30 a9 ee 91 85 38 a9 8c 00 85 3a')
if rom[0x611d2:0x611d2+len(landing)]!=landing:raise ValueError('Unexpected lateral landing state')
root=Path('analysis/movement-progression-probe');observed=[]
for direction in ('left','right'):
 path=root/f'penalty-keeper-motion-{direction}-{direction}'/'mode-hooks.jsonl';raw=path.read_bytes();events=[json.loads(l) for l in raw.splitlines()]
 if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 selectors=[e for e in events if e.get('site')=='penalty_selector_write' and e.get('d')==0x500 and e.get('animation_state')==0x91ac and e.get('old')==30 and e.get('value')==14]
 if len(selectors)!=1:raise ValueError('Unexpected selector observation')
 selector=selectors[0];frame=selector['frame']
 def one(site,at):
  found=[e for e in events if e.get('site')==site and e.get('frame')==at and e.get('d')==0x6c0]
  if len(found)!=1:raise ValueError('Missing movement observation')
  return found[0]
 before=one('keeper_move_end',frame-1);after=one('keeper_move_start',frame)
 if before['linked']!=0x500 or after['linked']!=0x500 or ((before['linked_flags']|0x2000)&0xfff7)!=after['linked_flags'] or before['vz']!=0 or after['vz']!=before['stored_jump']:raise ValueError('Transition mismatch')
 landed_before=one('keeper_move_end',9818);landed_after=one('keeper_move_start',9819)
 if ((landed_before['z']>>8)&0xffff)!=0 or landed_before['linked_flags']&0x2000==0 or landed_after['linked_flags']!=(landed_before['linked_flags']&0xdffd):raise ValueError('Unexpected landing transition')
 observed.append({'direction':direction,'frame':frame,'hooks_sha256':hashlib.sha256(raw).hexdigest(),'selector_old':selector['old'],'selector_new':selector['value'],'flags_before':before['linked_flags'],'flags_after':after['linked_flags'],'vz_before':before['vz'],'vz_after':after['vz'],'landing':{'frame':9819,'height_before':(landed_before['z']>>8)&0xffff,'flags_before':landed_before['linked_flags'],'flags_after':landed_after['linked_flags']}})
report={'schema':'issd-penalty-keeper-dive-flags/v1','rom_offsets':['0x611ac','0x611d2'],'routines':['8C:91AC','8C:91D2'],'observed':observed,'limits':['Two replays of one synthetic saved state and two-player RAM override.','Selector hook precedes the flag writes; landing and flag writes were not individually instrumented.','The transition into this animation state and its timing are not determined here.','The central animation takes another path. ROM and raw traces remain local.']}
Path('docs/issd-penalty-keeper-dive-flags.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('OK: lateral animation routine and two correlated flag transitions')
