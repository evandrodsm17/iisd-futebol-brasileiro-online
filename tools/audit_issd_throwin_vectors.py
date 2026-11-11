"""Audit six captured throw-in release vectors against the local USA ROM."""
import argparse
import hashlib
import json
from pathlib import Path
from render_issd_descriptor_sprite import span

EXPECTED='d2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9'
CASES={'A-Down':(8,64,20),'A-Left':(13,64,20),'A-Right':(3,64,20),
       'A-Up':(30,64,20),'B-Down':(8,56,15),'B-Up':(30,56,15)}


def read(path):
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows or rows[-1].get('type')!='done': raise ValueError(f'Incomplete trace: {path}')
    return rows


def audit(root,rom_path):
    rom=rom_path.read_bytes();digest=hashlib.sha256(rom).hexdigest()
    if digest!=EXPECTED:raise ValueError('Unexpected ROM revision')
    neutral=read(root/'NEUTRAL-NEUTRAL'/'release-hooks.jsonl')
    if any(r.get('address')=='85EF51' for r in neutral):raise ValueError('Neutral control unexpectedly released')
    results=[]
    for case,(angle,magnitude,kind) in CASES.items():
        path=root/case/'release-hooks.jsonl';rows=read(path)
        def one(name):
            items=[x for x in rows if x.get('frame')==2271 and x.get('address')==name]
            if len(items)!=1:raise ValueError(f'Missing or ambiguous {case} {name}')
            return items[0]
        entry,stored,release=one('839E32'),one('83953F'),one('85F8B9')
        if (entry['a'],entry['y'],release['x'])!=(angle,magnitude,kind):raise ValueError(f'Unexpected input for {case}')
        raw=span(rom,0x81A5D7+(angle&31)*4,4)
        coefficients=[int.from_bytes(raw[i:i+2],'little',signed=True) for i in (0,2)]
        values=[coefficients[0]*magnitude*(-1 if ((angle+16)&63)>=32 else 1),
                coefficients[1]*magnitude*(-1 if angle>=32 else 1)]
        expected=[[(value&0xffffffff)>>16,value&0xffff] for value in values]
        actual=[[stored['ball_vx'],stored['vx_fraction']],[stored['ball_vy'],stored['vy_fraction']]]
        if actual!=expected:raise ValueError(f'Velocity mismatch for {case}')
        results.append({'case':case,'angle':angle,'magnitude':magnitude,'ball_type':kind,
                        'coefficients':coefficients,'velocity_words':actual,
                        'trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'schema':'issd-throwin-vector-audit/v1','rom_sha256':digest,'frame':2271,'cases':results,
            'neutral_sha256':hashlib.sha256((root/'NEUTRAL-NEUTRAL'/'release-hooks.jsonl').read_bytes()).hexdigest(),
            'limitations':['One scenario and one replay state; no generalized input-to-angle or field scaling.',
                           'Only horizontal launch velocity; vertical motion, bounce and recipient are not established.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('--rom',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();report=audit(args.root,args.rom)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Validated',len(report['cases']),'launch vectors against ROM and replay')
