"""Extract the locally verified England home player palette as BGR555."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5,read_word,ROM_KIT_BANK,ROM_KIT_PTRS_HOME


def export(rom,detail):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];team=2;pointer=read_word(rom,ROM_KIT_PTRS_HOME+team*2)
    offset=ROM_KIT_BANK*0x8000+(pointer-0x8000)+2
    words=[read_word(rom,offset+i*2) for i in range(16)]
    entry=detail['teams'][team]['home']
    if entry['selector']!=4 or entry['bgr555']!=0x7800:raise ValueError('Unexpected detail selector')
    return {'schema':'issd-match-palette-local/v1','team':team,'kit':'home','skin':0,'words':words,'detail_bgr555':entry['bgr555'],
            'rom_sha256':hashlib.sha256(rom).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('detail',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=export(a.rom.read_bytes(),json.loads(a.detail.read_text(encoding='utf8')));a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,separators=(',',':')),encoding='utf8');print('Exported local verified palette')
