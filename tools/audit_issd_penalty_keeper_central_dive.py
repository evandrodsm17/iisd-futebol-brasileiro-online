"""Audit the central penalty keeper's observed animation and flag transition."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
code=bytes.fromhex('a0 d7 e7 a9 a0 e7 20 8f a6 a0 d0 de 84 1e 20 2d 95 a9 00 20 04 30 a9 04 00 14 30 a9 de 92 85 38 a9 8c 00 85 3a 6b')
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x612b8:0x612b8+len(code)]!=code:raise ValueError('Unexpected central animation routine')
path=Path('analysis/movement-progression-probe/penalty-keeper-motion-neutral-neutral/mode-hooks.jsonl');raw=path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
def one(site,frame):
 result=[(i,e) for i,e in enumerate(events) if e.get('site')==site and e.get('frame')==frame and e.get('side')==0 and e.get('round')==1]
 if len(result)!=1:raise ValueError(f'Ambiguous {site}')
 return result[0]
_,before=one('collision_miss',9794);selector_i,selector=one('penalty_selector_write',9795);move_i,move=one('keeper_move_start',9795);after_i,after=one('collision_miss',9795)
if not(selector_i<move_i<after_i and selector['d']==before['dp']==after['dp']==0x500 and move['linked']==0x500 and move['d']==0x6c0 and selector['animation_state']==0x92b8 and selector['old']==28 and selector['value']==20):raise ValueError('Unexpected objects or ordering')
if before['object_flags']!=0x16 or after['object_flags']!=0x12 or (move['linked_flags']&0x20ff)!=0x2012 or after['object_flags']!=(before['object_flags']&0xfb):raise ValueError('Unexpected flag transition')
report={'schema':'issd-penalty-keeper-central-dive/v1','rom_offset':'0x612b8','routine':'8C:92B8','hooks_sha256':hashlib.sha256(raw).hexdigest(),'observed':{'before_frame':9794,'transition_frame':9795,'selector_before':28,'selector_after':20,'flags_low_before':before['object_flags'],'flags_low_after':after['object_flags'],'linked_flags_after':move['linked_flags'],'velocity_after':move['vz']},'limits':['One replay of one synthetic saved state with player-count override.','Only the low byte of flags was captured before the transition.','The flag writes were not hooked individually; selector and movement hooks bracket them.','The end of the central dive was not captured. ROM and raw traces remain local.']}
Path('docs/issd-penalty-keeper-central-dive.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('OK: central animation and captured flag transition')
