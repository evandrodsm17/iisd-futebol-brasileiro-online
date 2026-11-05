"""Add ROM-derived initial team palettes to an existing local pass resource."""
import argparse, hashlib, json
from pathlib import Path
from export_issd_jump_directions import palettes
from extract_issd_catalog import EXPECTED_MD5

def update(asset_path,rom_path):
    raw=rom_path.read_bytes()
    data=json.loads(asset_path.read_text(encoding='utf8'))
    if len(raw)!=0x200000 or hashlib.md5(raw).hexdigest()!=EXPECTED_MD5: raise ValueError('ROM incompatível')
    if data.get('schema')!='issd-pass-body-local/v2' or data.get('rom_sha256')!=hashlib.sha256(raw).hexdigest(): raise ValueError('Recurso de passe incompatível com a ROM')
    data['palette10'],data['team_palette']=palettes(raw)
    asset_path.write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    return len(data['team_palette'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--asset',type=Path,required=True);parser.add_argument('--rom',type=Path,required=True)
    args=parser.parse_args();print('OK: paletas locais de',update(args.asset,args.rom),'equipes atualizadas')
