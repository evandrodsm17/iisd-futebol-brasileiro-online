"""Export a shot body only after validating ROM geometry, VRAM, OAM and pixels."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive, SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_oam_pixels import compose, compare
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def export(root, rom_path, output):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != EXPECTED_MD5: raise ValueError('Unexpected ROM')
    draws = [json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines()]
    captures = {x['frame']: x for x in map(json.loads, (root/'slide-poses.jsonl').read_text().splitlines())}
    descriptors = [0xa617,0xa620,0xa629,0xa632,0xa63b,0xa644]
    frames, evidence, palette = [], [], None
    for descriptor in descriptors:
        candidates = [g for g in draws if g.get('type')=='body_geometry' and g['object']==0x1900 and g['script']==0xd007 and g['descriptor']==descriptor and g['frame']+2 in captures and g['frame']+1 in captures and captures[g['frame']+1]['descriptor']==descriptor]
        if not candidates: raise ValueError(f'Missing geometry {descriptor:04X}')
        g=candidates[0]; f=g['frame']+1; prepared=captures[f]; shown=captures[f+1]
        if g['source']!='rom88' or g['parts']!=rom_parts(rom,g['pose']): raise ValueError('ROM geometry mismatch')
        events=[r for r in draws if not r.get('type') and r['frame']==f-1]
        i=next(i for i,r in enumerate(events) if r['object']==0x1900)
        parts=derive(g,g,prepared['obsel'],slots(events[i]['stack'],events[i+1]['stack']))
        stem=shown['stem']; ppu=(root/(stem+'-ppu.bin')).read_bytes(); vram=(root/(stem+'-vram.bin')).read_bytes(); cgram=(root/(stem+'-ppu-cgram.bin')).read_bytes()
        for part in parts:
            i=part['slot'];x,y,tile,attr=ppu[i*4:i*4+4]; high=(ppu[512+i//4]>>(2*(i%4)))&3
            actual={'slot':i,'x':x-(512 if high&1 else 0),'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][high>>1]}
            if part!=actual or (attr>>1)&7!=1: raise ValueError('OAM or palette mismatch')
        tiles,_=descriptor_tiles(rom,descriptor)
        for part in g['parts']:
            for y in range(2 if part['large'] else 1):
                for x in range(2 if part['large'] else 1):
                    tile=part['tile']+x+16*y
                    address=(((prepared['obsel']&7)<<9)+(((prepared['obsel']&0x18)+8)<<5)+((g['tile_base']+tile)&255))&2047
                    if tile>=24 or vram[address*32:address*32+32]!=tiles[tile*32:tile*32+32]: raise ValueError('VRAM tile mismatch')
        pixels=compose(ppu,vram,cgram,prepared['obsel'],[p['slot'] for p in parts])
        with Image.open(root/(stem+'-screen.png')) as image: quality=compare(pixels,image)
        if not quality['candidate_pixels'] or quality['nonmatching_pixels']: raise ValueError('Screenshot mismatch')
        colors=[int.from_bytes(cgram[(144+i)*2:(145+i)*2],'little') for i in range(16)]
        if palette is not None and colors!=palette: raise ValueError('Palette changed')
        palette=colors; inherited=g['object_inherited'] if g['object_inherited']&0x80 else g['global_prop']
        frames.append({'descriptor':descriptor,'props':g['object_prop']|(inherited&0x30)|(g['object_flags']&0xf0),'origin_x':48,'origin_y':68,'parts':g['parts'],'tiles':base64.b64encode(tiles).decode('ascii')})
        evidence.append({'descriptor':descriptor,'prepared_frame':f,'displayed_frame':f+1,'parts':len(parts),**quality})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':'issd-shot-body-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'screen_direction':2,'palette':palette,'width':96,'height':96,'frames':frames},separators=(',',':')),encoding='utf8')
    return {'schema':'issd-shot-body-evidence/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'screen_direction':2,'rom_direction':0,'frames':evidence,'limitations':['One actor, appearance, direction and replay; timing, hair and other directions need validation.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();a.report.write_text(json.dumps(export(a.root,a.rom,a.output),indent=2)+'\n',encoding='utf8')
