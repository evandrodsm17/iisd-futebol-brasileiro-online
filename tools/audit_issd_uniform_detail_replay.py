"""Compare actor-dependent ROM detail tiles with same-replay PPU VRAM."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def audit(rom,root,bridge):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    contexts={(r['step'],r['context']):r for r in rows if r.get('type')=='aux_execution'}
    frames=[]
    for f in bridge['frames']:
        context=contexts[(f['step'],0x0bd0)]
        if context['parent_y']!=0x1700 or context['parent_desc']!=f['descriptor']:raise ValueError('Actor/descriptor mismatch')
        actor={'type':context['parent_type'],'kit_variant':context['parent_kit_variant'],
               'uniform_selector':context['parent_uniform_selector'],'object_flags':context['parent_flags']}
        tiles,meta=descriptor_tiles(rom,f['descriptor'],actor)
        vram=(root/f"frame-{f['ppu_step']:03d}-vram.bin").read_bytes()
        base=((f['obsel']&7)<<9)+(((((f['obsel']&0x18)+8)<<5)) if f['bank'] else 0)
        address=((base+((f['base_tile']+23)&255))&2047)*32
        expected=vram[address:address+32]
        if tiles[23*32:24*32]!=expected:raise ValueError(f"Detail mismatch at step {f['step']}")
        frames.append({'step':f['step'],'descriptor':f['descriptor'],'actor':actor,'detail_byte':meta['detail'],
                       'detail_source':meta['detail_source'],'tile_sha256':hashlib.sha256(expected).hexdigest()})
    if not frames:raise ValueError('No evidence')
    return {'schema':'issd-uniform-detail-replay/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'trace_sha256':hashlib.sha256((root/'hair-runtime.jsonl').read_bytes()).hexdigest(),'frames':frames,
            'limitations':['One actor, team, kit, direction and replay. Actor position changed in isolated RAM.',
                           'Types 7/8/9 and other selector paths are not established by this comparison.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('capture',type=Path);p.add_argument('bridge',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.rom.read_bytes(),a.capture,json.loads(a.bridge.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Matched {len(r['frames'])} detail tiles")
