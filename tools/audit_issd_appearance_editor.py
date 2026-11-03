"""Cross-check original roster appearance bytes against the published editor contract."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import ROM_ATTR_BASE, PLAYERS_PER_TEAM, ATTR_BYTES, EXPECTED_MD5


def analyze(rom, catalog):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected the original USA ROM')
    skins, hairs=Counter(),Counter()
    teams=catalog.get('teams',[])
    if len(teams)!=36:raise ValueError('Expected 36 teams')
    for team_id,team in enumerate(teams):
        if team['id']!=team_id or len(team['players'])!=PLAYERS_PER_TEAM:raise ValueError('Unexpected roster')
        for slot,player in enumerate(team['players']):
            byte=rom[header+ROM_ATTR_BASE+(team_id*PLAYERS_PER_TEAM+slot)*ATTR_BYTES+6]
            if player['appearance']!={'skin_tone':byte>>4,'hair_style':byte&15}:
                raise ValueError(f'Appearance mismatch team={team_id} slot={slot}')
            skins[byte>>4]+=1;hairs[byte&15]+=1
    if set(skins)-{0,1} or set(hairs)-set(range(14)):
        raise ValueError('Values exceed the editor contract')
    pointers=[]
    for i in range(13):
        at=header+0xed6d+i*4
        addr=int.from_bytes(rom[at:at+3],'little')
        if (addr&0xffff)<0x8000:raise ValueError('Invalid hairstyle LoROM pointer')
        offset=((addr>>16)&0x7f)*0x8000+(addr&0x7fff)
        if offset+0x300>len(rom)-header:raise ValueError('Hair atlas exceeds ROM')
        pointers.append({'style':i+1,'pointer_table_offset':f'0x{0xed6d+i*4:X}',
                         'snes_address':f'${addr:06X}','lorom_offset':f'0x{offset:X}'})
    return {'schema':'issd-editor-appearance-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'catalog_players':sum(skins.values()),'record_offset':'0x50000 + (team * 20 + slot) * 7 + 6',
            'skin_variant_counts':dict(sorted(skins.items())),'hair_style_counts':dict(sorted(hairs.items())),
            'hair_atlases':pointers,'reference':{'repository':'https://github.com/EstebanFuentealba/web-snes-issd-studio',
            'commit':'229ec0bce3fcee580a5990cce333456f0700be99','files':['src/rom/deluxe.mjs','src/rom/players.mjs','src/rom/appearance.mjs','src/rom/player-preview.mjs']},
            'limitations':['Editor preview is not a validation of match-time composition.',
             'Skin and hair colors may be shared palette entries; the nibble is not an independent RGB color.',
             'Catalog skins and hair values do not prove every runtime sprite or team palette combination.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('catalog',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=analyze(a.rom.read_bytes(),json.loads(a.catalog.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Verified {result['catalog_players']} appearance records and {len(result['hair_atlases'])} atlas pointers")
