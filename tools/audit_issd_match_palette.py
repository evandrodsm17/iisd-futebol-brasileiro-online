"""Compare a ROM kit palette and detail color against same-replay CGRAM."""
import argparse
import hashlib
import json
from pathlib import Path
from export_issd_match_palette import export


def audit(rom,detail,root,bridge):
    palette=export(rom,detail);results=[]
    for f in bridge['frames']:
        c=(root/f"frame-{f['ppu_step']:03d}-cgram.bin").read_bytes()
        if len(c)!=512:raise ValueError('Invalid CGRAM')
        words=[int.from_bytes(c[(128+16+i)*2:(128+16+i)*2+2],'little') for i in range(16)]
        secondary=int.from_bytes(c[(128+5*16+12)*2:(128+5*16+13)*2],'little')
        if words!=palette['words'] or secondary!=palette['detail_bgr555']:raise ValueError(f"Palette mismatch {f['step']}")
        results.append({'step':f['step'],'descriptor':f['descriptor']})
    if not results:raise ValueError('No palette observations')
    return {'schema':'issd-match-palette-audit/v1','rom_sha256':palette['rom_sha256'],
            'capture_sha256':hashlib.sha256((root/'hair-runtime.jsonl').read_bytes()).hexdigest(),
            'team':2,'kit':'home','skin':0,'body_bank':1,'detail_bank':5,'detail_index':12,'samples':results,
            'limitations':['One replay and actor; original team/kit other than England home are not validated.',
                           'Other entries in the secondary bank remain capture data.',
                           'Actor skin value is not independently established by this palette comparison.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('detail',type=Path);p.add_argument('capture',type=Path);p.add_argument('bridge',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.rom.read_bytes(),json.loads(a.detail.read_text(encoding='utf8')),a.capture,json.loads(a.bridge.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Matched palette in {len(r['samples'])} samples")
