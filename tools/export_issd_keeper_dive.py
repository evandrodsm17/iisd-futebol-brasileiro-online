"""Export three goalkeeper dive poses validated against an isolated replay.

The replay positions the goalkeeper and ball synthetically. It demonstrates
rendered poses, not the original AI's trigger or general dive directions.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive, SIZES
from compare_issd_oam_pixels import compose, compare
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def export(root, rom_path, output, direction=0):
    rom=rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5: raise ValueError('Unexpected ROM')
    draws=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
    captures={x['frame']:x for x in map(json.loads,(root/'slide-poses.jsonl').read_text(encoding='utf8').splitlines())}
    frames=[];evidence=[];palette=None
    if direction not in (0,3,4,7):raise ValueError('Unsupported captured direction')
    descriptors={0:(0xcb42,0xcb4c,0xcb56),3:(0xcbbf,0xcbc9,0xcbd3),4:(0xcb5b,0xcb65,0xcb6f),7:(0xcb10,0xcb1a,0xcb24)}[direction]
    for frame,descriptor in zip((3799,3800,3807),descriptors):
        g=next(x for x in draws if x.get('type')=='body_geometry' and x['frame']==frame and x['object']==0x500)
        prepared=captures[frame+1];shown=captures[frame+2]
        if g['source']!='wram' or g['descriptor']!=descriptor or prepared['descriptor']!=descriptor or prepared['direction']!=direction: raise ValueError('Unexpected keeper pose')
        tiles,meta=descriptor_tiles(rom,descriptor)
        if int(meta['pose'][1:],16)!=g['pose']: raise ValueError('ROM pose pointer mismatch')
        events=[x for x in draws if not x.get('type') and x['frame']==frame]
        i=next(i for i,x in enumerate(events[:-1]) if x['object']==0x500)
        parts=derive(g,g,prepared['obsel'],slots(events[i]['stack'],events[i+1]['stack']))
        stem=shown['stem'];ppu=(root/(stem+'-ppu.bin')).read_bytes();vram=(root/(stem+'-vram.bin')).read_bytes();cgram=(root/(stem+'-ppu-cgram.bin')).read_bytes()
        for part in parts:
            i=part['slot'];x,y,tile,attr=ppu[4*i:4*i+4];high=(ppu[512+i//4]>>(2*(i%4)))&3
            actual={'slot':i,'x':x-(512 if high&1 else 0),'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][high>>1]}
            if part!=actual or (attr>>1)&7!=4 or attr&1: raise ValueError('OAM differs from observed first-bank keeper geometry')
        for part in g['parts']:
            for y in range(2 if part['large'] else 1):
                for x in range(2 if part['large'] else 1):
                    tile=part['tile']+x+16*y;address=((prepared['obsel']&7)<<9)+((g['tile_base']+tile)&255)
                    if tile>=24 or vram[address*32:address*32+32]!=tiles[tile*32:tile*32+32]:raise ValueError('ROM/VRAM tile mismatch')
        pixels=compose(ppu,vram,cgram,prepared['obsel'],[part['slot'] for part in parts])
        with Image.open(root/(stem+'-screen.png')) as image:
            quality=compare(pixels,image)
            if not quality['candidate_pixels']:raise ValueError('Empty screenshot')
            if quality['nonmatching_pixels']:
                image=image.convert('RGB');full=compose(ppu,vram,cgram,prepared['obsel'],list(range(128)))
                if any(full.get(xy)!=image.getpixel(xy) for xy,rgb in pixels.items() if image.getpixel(xy)!=rgb):raise ValueError('Unexplained screenshot mismatch')
        colors=[int.from_bytes(cgram[(192+i)*2:(193+i)*2],'little') for i in range(16)]
        if palette is not None and colors!=palette:raise ValueError('Keeper palette changed')
        palette=colors;inherited=g['object_inherited'] if g['object_inherited']&0x80 else g['global_prop']
        frames.append({'descriptor':descriptor,'props':g['object_prop']|(inherited&0x30)|(g['object_flags']&0xf0),'origin_x':48,'origin_y':68,'parts':g['parts'],'tiles':base64.b64encode(tiles).decode('ascii')})
        evidence.append({'descriptor':descriptor,'prepared_frame':frame+1,'displayed_frame':frame+2,'slots':[part['slot'] for part in parts],'parts':len(parts),**quality})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':'issd-keeper-dive-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'width':96,'height':96,'palette':palette,'ticks':[1,7,28],'frames':frames},separators=(',',':')),encoding='utf8')
    return {'schema':'issd-keeper-dive-evidence/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'synthetic_setup':True,'forced_direction':direction!=0,'rom_direction':direction,'frames':evidence,'limitations':['One synthetic trajectory, goalkeeper and appearance.','Nonzero direction was forced in emulator memory; it does not demonstrate a naturally triggered dive.','First descriptor began with one stale pose; ticks are observed state durations, not fully validated visual timing.','Does not validate AI, collision or other teams.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--direction',type=int,default=0);a=p.parse_args()
    a.report.write_text(json.dumps(export(a.root,a.rom,a.output,a.direction),indent=2)+'\n',encoding='utf8')
