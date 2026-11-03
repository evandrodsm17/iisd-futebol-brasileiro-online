"""Extract the ROM's team/kit-specific color write used at OBJ palette index 12."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def extract(rom):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    data=rom[header:];team_base=0x10459;colors_base=0x4832a
    teams=[]
    for team in range(36):
        kits={}
        for kit,delta in (('home',0),('away',1)):
            selector=data[team_base+team*2+delta]
            if selector and (selector%2 or selector>0x16):raise ValueError('Unexpected color selector')
            value=int.from_bytes(data[colors_base+selector:colors_base+selector+2],'little') if selector else None
            kits[kit]={'selector':selector,'bgr555':value}
        teams.append({'team_id':team,**kits})
    return {'schema':'issd-team-detail-colors/v1','rom_sha256':hashlib.sha256(data).hexdigest(),
            'selector_lorom_offset':'0x10459','colors_lorom_offset':'0x4832A',
            'teams':teams,'limitations':['Selector zero means this routine does not write the color; prior palette state remains.',
             'The relationship to gameplay appearance is validated only for the observed England home case.',
             'Match initialization and later palette updates may alter the final PPU color.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=extract(a.rom.read_bytes());a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Extracted {len(result['teams'])} teams, including no-write selectors")
