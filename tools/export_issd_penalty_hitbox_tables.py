"""Extract local penalty contact tables and audit the observed selector samples."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_penalty_hitboxes import collision
from extract_issd_catalog import EXPECTED_MD5


def extract(rom_path, observed_path, local_path, report_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected unheadered ROM')
    gate=bytes.fromhex('ad aa 14 89 60 00 d0 5a 0b a5 36 5b a6 14 bf 6c bc 8c a8 a6 1a 20 75 a3 90 28 ad aa 14 89 00 01 f0 14 ad 06 17 c9 01 00 f0 0c c9 02 00 f0 07 c9 03 00 f0 02 80 0c 2b a9 0a 95 85 38 a9 8c 00 85 3a 6b 2b 6b')
    if rom[0x614c6:0x614c6+len(gate)]!=gate:
        raise ValueError('Unexpected contact gates and selection routine')
    expected=[0xde13,0xde19,0xde1f,0xde25,0xde2f,0xde35,0xde3b,0xde45,0xde4f,0xde59,0xde5f,0xde65,0xde6f,0xde75,0xde7f,0xde85]
    pointers=[int.from_bytes(rom[0x63c6c+i*2:0x63c6e+i*2],'little') for i in range(16)]
    if pointers!=expected:raise ValueError('Unexpected contact table pointers')
    tables=[]
    for index,pointer in enumerate(pointers):
        end=int.from_bytes(rom[pointer:pointer+2],'little')
        if not pointer+2<end<=0xde8e:raise ValueError('Invalid native table bounds')
        rectangles=[]
        for cursor in range(pointer+2,end,4):
            if cursor+4>len(rom):raise ValueError('Missing adjacent native bytes')
            rectangles.append(list(rom[cursor:cursor+4]))
        tables.append({'selector':index*2,'pointer':pointer,'end':end,'rectangles':rectangles})
    observed_raw=observed_path.read_bytes();observed=json.loads(observed_raw)
    if observed['schema']!='issd-penalty-selector/v1' or len(observed['samples'])!=8:raise ValueError('Unexpected captured selector audit')
    for sample in observed['samples']:
        table=tables[sample['selector']//2]
        if sample['selector']!=table['selector'] or sample['table_pointer']!=table['pointer'] or collision(rom,sample)!=(sample['site']=='collision_hit'):
            raise ValueError(f"Captured selector or geometry mismatch at frame {sample['frame']}")
    asset={'schema':'issd-penalty-hitbox-tables/v1','tables':tables}
    local_path.parent.mkdir(parents=True,exist_ok=True)
    local_path.write_text(json.dumps(asset,indent=2)+'\n',encoding='utf8')
    report={'schema':'issd-penalty-hitbox-local-export/v1','source_audit_sha256':hashlib.sha256(observed_raw).hexdigest(),
            'local_asset_sha256':hashlib.sha256(local_path.read_bytes()).hexdigest(),
            'table_count':len(tables),'observed_checks':len(observed['samples']),
            'unaligned_selector':30,'unaligned_end':tables[15]['end'],
            'limits':['Selector and rectangles are native values, not screen coordinates or named animations.',
                      'Eight captured checks are sampled from one synthetic shootout.',
                      'An unaligned end needs the adjacent ROM byte because the original loop reads four bytes.',
                      'ROM and extracted data remain local.']}
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','observed','local','report'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=extract(args.rom,args.observed,args.local,args.report)
    print(f"OK: {report['table_count']} native tables, {report['observed_checks']} captured checks")
