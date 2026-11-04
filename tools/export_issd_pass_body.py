"""Export locally reconstructed ROM tiles for two validated normal-B body poses."""
import argparse,base64,hashlib,json
from pathlib import Path
from audit_issd_normal_b_body import audit
from render_issd_descriptor_sprite import descriptor_tiles


def export(root,control,rom_path,state,output):
    report=audit(root,control,rom_path,state);rom=rom_path.read_bytes()
    draws=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()]
    captures={r['frame']:r for x in (root/'slide-poses.jsonl').read_text().splitlines() if (r:=json.loads(x))}
    frames=[];palette=None
    for entry in report['frames']:
        g=next(r for r in draws if r.get('type')=='body_geometry' and r['frame']==entry['draw_frame'] and r['object']==0x1900)
        capture=captures[entry['displayed_frame']];vram=(root/(capture['stem']+'-vram.bin')).read_bytes();cgram=(root/(capture['stem']+'-ppu-cgram.bin')).read_bytes()
        colors=[int.from_bytes(cgram[(144+i)*2:(145+i)*2],'little') for i in range(16)]
        if palette is not None and palette!=colors:raise ValueError('Unexpected palette change')
        palette=colors;tiles,_=descriptor_tiles(rom,entry['descriptor']);base=g['tile_base']&255
        for part in g['parts']:
            size=16 if part['large'] else 8
            for y in range(size//8):
                for x in range(size//8):
                    index=part['tile']+x+16*y
                    if index>=24:raise ValueError('Unexpected tile index')
                    address=(((capture['obsel']&7)<<9)+(((capture['obsel']&0x18)+8)<<5)+((base+index)&255))&2047
                    if vram[address*32:address*32+32]!=tiles[index*32:index*32+32]:raise ValueError('ROM tiles differ from VRAM')
        inherited=g['object_inherited'] if g['object_inherited']&0x80 else g['global_prop']
        props=g['object_prop']|(inherited&0x30)|(g['object_flags']&0xf0)
        frames.append({'descriptor':entry['descriptor'],'props':props,'origin_x':48,'origin_y':68,'parts':g['parts'],'tiles':base64.b64encode(tiles).decode('ascii')})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':'issd-pass-body-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'team':2,'kit':'home','skin':0,'hair':0,'screen_direction':2,'ticks':[2,16],'palette':palette,'width':96,'height':96,'frames':frames,'limitations':['Two body poses from one neutral-direction B replay.','Hair style and command context require further runtime validation.','ROM-derived graphics are local only.']},separators=(',',':')),encoding='utf-8')
    return len(frames)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--control',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print('local ROM body frames:',export(a.root,a.control,a.rom,a.state,a.output))
