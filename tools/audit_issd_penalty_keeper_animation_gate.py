"""Check known animation gate instructions and observed selector transitions."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
fixtures={0x61196:'20 a3 a6 90 0a a9 ac 91 85 38 a9 8c 00 85 3a a0 bb de 20 2d 95 6b',0x626a3:'8d 18 00 20 ce a6 0b 5b ad 18 00 22 a0 e8 84 f0 06 2b 20 f5 a6 18 60 2b 20 f5 a6 38 60',0x265d1:'c6 16 d0 07 a5 18 30 04 a9 00 00 60',0x265dd:'8b f4 00 82 ab ab a5 1a 4a a8 a9 00 80 04 16 b1 18 aa 29 00 ff d0 05 a9 00 80 14 18 8a 80 55',0x26651:'29 ff 00 80 39',0x2668f:'85 16 a5 2e 0a a8 b1 1c a8 b1 1a 10 07 e6 1a e6 1a aa 80 24 64 1a 09 00 80 aa 80 1c',0x16dde:'03 03 03 00 04 0f ff 00 f4 ed ee ed fa ed 00 ee 18 ee 20 ee 28 ee 18 ee 50 ee 58 ee'}
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
for offset,signature in fixtures.items():
 expected=bytes.fromhex(signature)
 if rom[offset:offset+len(expected)]!=expected:raise ValueError(f'Unexpected ROM at {offset:#x}')
root=Path('analysis/movement-progression-probe');observed=[]
for direction in ('left','right'):
 raw=(root/f'penalty-keeper-motion-{direction}-{direction}'/'mode-hooks.jsonl').read_bytes();events=[json.loads(line) for line in raw.splitlines()]
 if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
 selectors=[e for e in events if e.get('site')=='penalty_selector_write' and e.get('d')==0x500 and e.get('side')==0 and e.get('round')==1 and e.get('value') in (28,30,14) and 9780<=e.get('frame',0)<=9800]
 if [(e['frame'],e['value'],e['animation_state']) for e in selectors]!=[(9792,28,0x918c),(9795,30,0x918c),(9799,14,0x91ac)]:raise ValueError('Unexpected selector sequence')
 observed.append({'direction':direction,'hooks_sha256':hashlib.sha256(raw).hexdigest(),'selector_frames':[e['frame'] for e in selectors],'selectors':[e['value'] for e in selectors],'states':[e['animation_state'] for e in selectors]})
report={'schema':'issd-penalty-keeper-animation-gate/v1','rom_offsets':[hex(i) for i in fixtures],'observed':observed,'limits':['Two replays of one synthetic saved state with player-count override.','Selector writes were captured; helper counter, table variant and entry timing were not recorded.','The reload is modeled up to graphics dispatch; the returned flags are not modeled.','Frame intervals are observations, not general timing rules.']}
Path('docs/issd-penalty-keeper-animation-gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('OK: animation gate bytes and two selector timelines')
