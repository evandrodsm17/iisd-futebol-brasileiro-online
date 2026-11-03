"""Match descriptor-selected ROM hair tiles to same-frame OAM/VRAM."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import lorom_offset


def audit(rom,root,bridge,style):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    if style not in (1,2,13):raise ValueError('Style not captured')
    rom=rom[header:];raw=(root/'hair-runtime.jsonl').read_bytes()
    rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    contexts={(r['step'],r['context']):r for r in rows if r.get('type')=='aux_execution'}
    address=int.from_bytes(rom[0xed6d+(style-1)*4:0xed70+(style-1)*4],'little')
    atlas=lorom_offset(address);result=[]
    for f in bridge['frames']:
        context=contexts[(f['step'],0x0bd0)]
        if context['parent_y']!=0x1700 or context['parent_desc']!=f['descriptor'] or context['hair_offset']!=(style-1)*4:raise ValueError('Hair context mismatch')
        selector=rom[0x10000+(f['descriptor']&0x7fff)+8]
        if not 1<=selector<=24:raise ValueError('Unexpected hair selector')
        stem=root/f"frame-{f['ppu_step']:03d}"
        oam=Path(str(stem)+'-oam.bin').read_bytes();vram=Path(str(stem)+'-vram.bin').read_bytes()
        slot=f['hair_slot'];tile=oam[slot*4+2];attr=oam[slot*4+3]
        high=(oam[512+slot//4]>>(2*(slot%4)))&3
        if high&2:raise ValueError('Expected 8x8 hair entry')
        base=((f['obsel']&7)<<9)+(((((f['obsel']&0x18)+8)<<5)) if attr&1 else 0)
        destination=((base+tile)&2047)*32;expected=rom[atlas+(selector-1)*32:atlas+selector*32]
        if expected!=vram[destination:destination+32]:raise ValueError(f"Hair tile mismatch step {f['step']}")
        result.append({'step':f['step'],'descriptor':f['descriptor'],'selector':selector,'slot':slot,'vram_offset':destination})
    return {'schema':'issd-hair-descriptor-replay/v1','style':style,'rom_sha256':hashlib.sha256(rom).hexdigest(),
            'trace_sha256':hashlib.sha256(raw).hexdigest(),'frames':result,
            'limitations':['One actor, kit, direction and replay; position and styles 2/13 changed in isolated RAM.',
                           'OAM placement and palettes remain captured; no general appearance selection is established.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('capture',type=Path);p.add_argument('bridge',type=Path);p.add_argument('--style',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.rom.read_bytes(),a.capture,json.loads(a.bridge.read_text(encoding='utf8')),a.style)
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Matched {len(r['frames'])} hair tiles, style {a.style}")
