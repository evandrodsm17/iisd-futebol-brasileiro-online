"""Check the penalty keeper jump gate against ROM and observed state changes."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
expected=bytes.fromhex('a4 36 b9 30 00 89 08 00 d0 16 a5 30 89 08 00 f0 0a a5 20 85 2b a5 21 85 2c 64 20 a9 6c 94 85 38')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x6144c:0x6144c+len(expected)]!=expected:raise ValueError('Unexpected keeper jump gate')
root=Path('analysis/movement-progression-probe');observed=[]
for direction in ('left','neutral','right'):
 path=root/f'penalty-keeper-motion-{direction}-{direction}'/'mode-hooks.jsonl';raw=path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
 if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 starts=[e for e in events if e.get('site')=='keeper_move_start'];init=[e for e in events if e.get('site')=='keeper_init_end']
 if len(init)!=1:raise ValueError('Missing initialization')
 jump=init[0]['stored_jump'];applied=[e for e in starts if e['vz']==jump and (e['stored_jump']&0xffff)==0]
 if len(applied)!=1:raise ValueError('Unexpected jump observation')
 first=applied[0];prior=next((e for e in reversed(starts) if e['frame']<first['frame']),None)
 if first['state_flags']&8==0 or first['linked_flags']&8 or first['stored_jump']!=(jump&0xff0000):raise ValueError('State inconsistent with gate')
 if prior and (prior['state_flags']&8==0 or prior['linked_flags']&8==0 or prior['vz']!=0 or prior['stored_jump']!=jump):raise ValueError('Unexpected prior state')
 observed.append({'direction':direction,'hooks_sha256':hashlib.sha256(raw).hexdigest(),'first_move_after_impulse':{'frame':first['frame'],'state_flags':first['state_flags'],'linked_flags':first['linked_flags'],'vz':first['vz'],'stored_jump':first['stored_jump']},'previous_move':None if prior is None else {'frame':prior['frame'],'state_flags':prior['state_flags'],'linked_flags':prior['linked_flags'],'vz':prior['vz'],'stored_jump':prior['stored_jump']}})
report={'schema':'issd-penalty-keeper-jump/v1','rom_offset':'0x6144c','routine':'8C:944C','observed':observed,'limits':['Three replays share one synthetic saved state and a two-player RAM override.','These hooks observe states around the gate, not its execution itself.','The source and timing of the linked flag change remain unverified.','ROM, saved state and raw traces remain local.']}
Path('docs/issd-penalty-keeper-jump.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('OK: keeper jump gate bytes and three observed transitions')
