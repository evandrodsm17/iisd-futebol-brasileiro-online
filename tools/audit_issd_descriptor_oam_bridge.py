"""Compare ROM descriptor uploads with same-frame captured player OAM pixels."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_oam_pixels import compose
from export_issd_team_motion import trace
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles,normalise_parts


def audit(rom,root,trace_path):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:]
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    graphics={r['frame']:r for r in rows if r.get('type')=='graphics'}
    draw={(r['step'],r['object']):r for r in rows if r.get('type')=='draw_entry'}
    audit_data=json.loads((root/'oam-audit.json').read_text(encoding='utf8'))
    observed={}
    for row in trace(trace_path):
        for actor in row.get('actors',[]):
            if actor['address']==0x0d00 and actor['direction']==4:
                observed.setdefault(actor['descriptor'],actor)
    results=[];skipped=[]
    for frame in audit_data['frames']:
        if frame['nonmatching_pixels'] or not frame['candidate_pixels']:continue
        step=frame['step'];body=draw.get((step,0x1700));graphic=graphics[frame['ppu_frame']]
        actor=observed.get(body['geometry_pointer'] and next((r['parent_desc'] for r in rows if r.get('type')=='aux_execution' and r['step']==step and r['context']==0x0bd0),None)) if body else None
        if not actor:skipped.append({'step':step,'reason':'missing_descriptor'});continue
        parts=normalise_parts(actor['parts']);slots=frame['body_slots']
        if len(parts)!=len(slots):skipped.append({'step':step,'reason':'part_count'});continue
        prefix=root/f"frame-{graphic['step']:03d}";read=lambda suffix:Path(str(prefix)+suffix).read_bytes()
        oam=read('-oam.bin');original=read('-vram.bin');cgram=read('-cgram.bin');obsel=graphic['obsel']
        bases=set();valid=True
        for p,slot in zip(parts,slots):
            x,y,tile,attr=oam[slot*4:slot*4+4];high=(oam[512+slot//4]>>(2*(slot%4)))&3
            if high&1:x-=512
            size=((8,16),(8,32),(8,64),(16,32),(16,64),(32,64),(16,32),(16,32))[obsel>>5][high>>1]
            if (x,y,size,attr&0xc0)!=(body['draw_x']+p['x'],(body['draw_y']+body['draw_z']+p['y'])%65536,p['size'],p['attr']&0xc0):valid=False;break
            bases.add(((tile-p['tile'])&255,attr&1))
        if not valid or len(bases)!=1:skipped.append({'step':step,'reason':'geometry_or_bank_mismatch'});continue
        base,bank=bases.pop();replacement=bytearray(original);source,meta=descriptor_tiles(rom,actor['descriptor'])
        tile_base=((obsel&7)<<9)+((((obsel&0x18)+8)<<5) if bank else 0)
        for tile in list(range(8))+list(range(16,23)):
            hardware=(base+tile)&255
            dest=((tile_base+hardware)&2047)*32
            replacement[dest:dest+32]=source[tile*32:(tile+1)*32]
        # Tile 23 may contain a uniform detail from a different ROM source;
        # it stays from the same PPU capture until its selector is resolved.
        expected=compose(oam,original,cgram,obsel,slots);actual=compose(oam,replacement,cgram,obsel,slots)
        if expected!=actual:
            skipped.append({'step':step,'reason':'pixel_mismatch','different_pixels':sum(expected.get(p)!=actual.get(p) for p in expected.keys()|actual.keys())});continue
        results.append({'step':step,'ppu_step':graphic['step'],'descriptor':actor['descriptor'],'base_tile':base,'bank':bank,
                        'body_slots':slots,'hair_slot':frame['hair_slot'],'obsel':obsel,
                        'parts':len(parts),'pixels':len(actual),'detail_byte':meta['detail']})
    if not results:raise ValueError('No matching descriptors')
    return {'schema':'issd-descriptor-oam-bridge/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),'frames':results,'skipped':skipped,
            'limitations':['One actor and direction; geometry from a different earlier trace.',
                           'OAM, palette and tile 23 come from same-frame capture; hair is not reconstructed here.',
                           'Exact pixels do not prove hidden pieces or gameplay timing.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('capture',type=Path);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.rom.read_bytes(),a.capture,a.trace);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Matched {len(result['frames'])} frames; skipped {len(result['skipped'])}")
