"""Export locally only the ROM hair tiles covered by replay evidence."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import lorom_offset


def export(rom,reports):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];sha=hashlib.sha256(rom).hexdigest();styles={}
    for report in reports:
        style=report['style']
        if report.get('schema')!='issd-hair-descriptor-replay/v1' or report['rom_sha256']!=sha or style not in (1,2,13) or str(style) in styles:raise ValueError('Incompatible hair evidence')
        frames=report['frames'];selectors={str(x['descriptor']):x['selector'] for x in frames}
        if len(selectors)!=10 or any(not 1<=x<=24 for x in selectors.values()):raise ValueError('Incomplete hair evidence')
        address=int.from_bytes(rom[0xed6d+(style-1)*4:0xed70+(style-1)*4],'little');offset=lorom_offset(address)
        tiles={str(n):base64.b64encode(rom[offset+(n-1)*32:offset+n*32]).decode('ascii') for n in set(selectors.values())}
        styles[str(style)]={'selectors':selectors,'tiles':tiles}
    if set(styles)!={'1','2','13'}:raise ValueError('Missing style evidence')
    return {'schema':'issd-hair-descriptor-tiles-local/v1','rom_sha256':sha,'styles':styles}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('reports',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=export(a.rom.read_bytes(),[json.loads(r.read_text(encoding='utf8')) for r in a.reports]);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,separators=(',',':')),encoding='utf8');print('Exported validated hair tiles locally')
