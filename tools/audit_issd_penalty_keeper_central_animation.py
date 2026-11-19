"""Check central keeper animation path, tables and captured selector changes."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
fixtures={0x61153:'a9 08 00 14 30 4c 7a 92',0x6127a:'20 74 a4 a9 6b e7 a0 5b e7 20 8f a6 a9 02 00 04 30 a0 c9 de 20 2d 95 a9 9c 92 85 38 a9 8c 00 85 3a 6b',0x6129c:'a9 a2 92 85 38 6b',0x612a2:'20 a3 a6 90 0a a9 b8 92 85 38 a9 8c 00 85 3a a0 c9 de 20 2d 95 6b',0x1675b:'78 e7 7e e7 84 e7 84 e7 78 e7 8a e7 72 e7 72 e7 02 01 01 00',0x16778:'e4 c9 e9 c9 ee c9',0xdec9:'1c 00 1c 00 1c 00 ff 14 00 16 00 ff'}
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
for offset,signature in fixtures.items():
 value=bytes.fromhex(signature)
 if rom[offset:offset+len(value)]!=value:raise ValueError(f'Unexpected bytes at {offset:#x}')
path=Path('analysis/movement-progression-probe/penalty-keeper-motion-neutral-neutral/mode-hooks.jsonl');raw=path.read_bytes();events=[json.loads(l) for l in raw.splitlines()]
if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete capture')
selected=[e for e in events if e.get('site')=='penalty_selector_write' and e.get('d')==0x500 and e.get('side')==0 and e.get('round')==1 and 9788<=e.get('frame',0)<=9795]
if [(e['frame'],e['value'],e['animation_state']) for e in selected]!=[(9789,28,0x9153),(9795,20,0x92b8)]:raise ValueError('Unexpected central selector sequence')
if any(e['bank']!=0x81 or not e['indexed_load'] or rom[e['source']]!=e['value'] for e in selected):raise ValueError('Unexpected selector source')
report={'schema':'issd-penalty-keeper-central-animation/v1','rom_offsets':[hex(offset) for offset in fixtures],'hooks_sha256':hashlib.sha256(raw).hexdigest(),'observed':{'frames':[e['frame'] for e in selected],'selectors':[e['value'] for e in selected],'states':[e['animation_state'] for e in selected],'banks':[e['bank'] for e in selected]},'limits':['One replay from a synthetic saved state with a player-count override.','Counter, graphics variant and initial helper state were not captured.','Matching a hypothetical sequence does not establish uniqueness or general timing.','ROM and raw traces remain local.']}
Path('docs/issd-penalty-keeper-central-animation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('OK: central animation path and selector observations')
