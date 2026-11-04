"""Verify slide palette sources against ROM tables and captured PPU colors."""
import argparse, hashlib, json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_team_detail_colors import extract


def verify(rom,data,analysis):
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    tables=[]
    for team in range(36):
        pointer=int.from_bytes(rom[0xe7d8+team*2:0xe7da+team*2],'little'); offset=0x48000+pointer-0x8000
        if int.from_bytes(rom[offset:offset+2],'little')!=7:raise ValueError('Team palette length mismatch')
        words=[int.from_bytes(rom[offset+2+i*2:offset+4+i*2],'little') for i in range(4)]
        if data['team_palette'][team]!=words:raise ValueError('Team palette mismatch')
        tables.append(words)
    goalie=[]
    for team in range(43):
        pointer=int.from_bytes(rom[0x10326+team*2:0x10328+team*2],'little');offset=0x48000+pointer-0x8000
        if int.from_bytes(rom[offset:offset+2],'little')!=21:raise ValueError('Goalkeeper palette length mismatch')
        goalie.append(int.from_bytes(rom[offset+20:offset+22],'little'))
    if set(goalie)!={data['palette10']}:raise ValueError('Index 10 is not invariant')
    expected12=extract(rom)['teams'][30]['home']['bgr555'];files=[]
    roots=[analysis/'slide-direction-paired/A'/name for name in ('Up','Right','DownRight','Down','DownLeft','Left','UpLeft')]+[analysis/'slide-upright-paired/A']
    for root in roots:
        for path in root.glob('*-ppu-cgram.bin'):
            cgram=path.read_bytes()
            if len(cgram)!=512:raise ValueError('Invalid CGRAM')
            word=lambda index:int.from_bytes(cgram[2*(192+index):2*(193+index)],'little')
            if word(10)!=data['palette10'] or word(12)!=expected12 or [word(i) for i in (13,14,15)]!=tables[30][1:]:raise ValueError('Captured PPU colors differ')
            files.append(path)
    if len(files)<8*30:raise ValueError('Insufficient captures')
    return {'schema':'issd-slide-palette-table-verification/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'team_palette_table':'$81:E7D8','team_palette_routine':'$A4:920B → $80:A4EF','team_palette_count':len(tables),
            'goalkeeper_palette_table':'$82:8326','goalkeeper_palette_routine':'$8B:D061 → $80:A4EF',
            'goalkeeper_palette_count':len(goalie),'goalkeeper_index_10_bgr555':data['palette10'],
            'capture_team':30,'capture_kit':'home','capture_cgram_samples':len(files),
            'limitations':['One match context verifies PPU colors; other teams use decoded ROM initialization tables.',
                           'Color updates after initialization may change actual PPU state.',
                           'Skin and uniform combinations have not all been captured in gameplay.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--directions',type=Path,required=True);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=verify(a.rom.read_bytes(),json.loads(a.directions.read_text(encoding='utf8')),a.analysis)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 36 team palettes, 43 goalkeeper entries,',result['capture_cgram_samples'],'CGRAM captures')
