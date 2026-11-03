"""Compare sheet anchors and reconstructed hair to observed gameplay OAM."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_hair_oam import analyze
from compare_issd_oam_pixels import compose,ppu_color
from render_issd_oam_composite import decode_tile
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import lorom_offset


def audit(rom,root,anchors,geometry,sheet_path,detail_output=None):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];report=analyze(root)
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    entries={(r['step'],r['object']):r for r in rows if r.get('type')=='draw_entry' and r.get('object') in (0x1700,0x0bd0)}
    graphics={r['frame']:r for r in rows if r.get('type')=='graphics'}
    contexts={(r['step'],r['context']):r for r in rows if r.get('type')=='aux_execution'}
    bypointer={v['pointer']:v for v in geometry['poses'].values()}
    direction=anchors['cycles']['walking'][4]; lookup={f['descriptor']:(i,f) for i,f in enumerate(direction['frames'])}
    color_map={(n*255)//31:(n<<3)|(n>>2) for n in range(32)}
    sheet=Image.open(sheet_path).convert('RGBA');frames=[];skipped=[];palette_rgb=None;detail_tiles={}
    for f in report['frames']:
        if f['nonmatching_pixels']:continue
        step=f['step'];body=entries[(step,0x1700)];hair=entries[(step,0x0bd0)];context=contexts[(step,0x0bd0)]
        meta=bypointer.get(hair['geometry_pointer'])
        if not meta or meta['descriptor'] not in lookup:
            skipped.append({'step':step,'reason':'outside_target_cycle'});continue
        index,anchor=lookup[meta['descriptor']]
        if context['hair_offset']!=0:raise ValueError('Unexpected hairstyle')
        ppu=graphics[f['ppu_frame']];stem=root/f"frame-{ppu['step']:03d}"
        read=lambda suffix:Path(str(stem)+suffix).read_bytes()
        oam,vram,cgram=read('-oam.bin'),read('-vram.bin'),read('-cgram.bin')
        observed_body=compose(oam,vram,cgram,ppu['obsel'],f['body_slots'])
        cell=sheet.crop((index*direction['cell_width'],0,(index+1)*direction['cell_width'],direction['cell_height']))
        bx=body['draw_x']-anchor['origin_x'];by=(body['draw_y']+body['draw_z'])%0x10000-anchor['origin_y']
        body_pixels={}
        for y in range(cell.height):
            for x in range(cell.width):
                pixel=cell.getpixel((x,y));px,py=x+bx,y+by
                if pixel[3] and 0<=px<256 and 0<=py<224:
                    body_pixels[(px,py)]=tuple(color_map[channel] for channel in pixel[:3])
        detail=None
        if body_pixels!=observed_body:
            # Some body OAM entries use a second palette. Existing sheets bake
            # all entries with the same palette, so restore only an observed,
            # independently verified 8x8 piece before comparing the full body.
            alternate=[slot for slot in f['body_slots'] if ((oam[slot*4+3]>>1)&7)!=1]
            if len(alternate)==1:
                slot=alternate[0];px,py,number,attr=oam[slot*4:slot*4+4]
                high=(oam[512+slot//4]>>(2*(slot%4)))&3
                if high==0:
                    piece=compose(oam,vram,cgram,ppu['obsel'],[slot]);candidate={**body_pixels,**piece}
                    if candidate==observed_body:
                        tile_base=((ppu['obsel']&7)<<9)+(((((ppu['obsel']&0x18)+8)<<5)) if attr&1 else 0)
                        indices=decode_tile(vram,tile_base+number);pal=(attr>>1)&7
                        detail={'x':px-body['draw_x'],'y':py-((body['draw_y']+body['draw_z'])%0x10000),
                                'h_flip':bool(attr&0x40),'v_flip':bool(attr&0x80),'palette':pal}
                        detail_tiles[str(step)]={'pixels':sum(indices,[]),
                          'palette_rgb':[list(ppu_color(cgram,128+pal*16+i)) for i in range(16)]}
                        body_pixels=candidate
        if body_pixels!=observed_body:
            common=set(body_pixels)&set(observed_body)
            skipped.append({'step':step,'reason':'body_pixels_differ','overlap':len(common),
                            'color_differences':sum(body_pixels[p]!=observed_body[p] for p in common),
                            'geometry_differences':len(set(body_pixels)^set(observed_body))})
            continue
        if not hair['object_flags']&0x40:
            skipped.append({'step':step,'reason':'unsupported_flip'});continue
        x=hair['draw_x']-meta['x']-4;y=(hair['draw_y']+hair['draw_z'])%0x10000+meta['y']-4
        recorded=f['hair_oam']
        if (x,y)!=(recorded['x_low'],recorded['y']) or not recorded['attr']&0x40:
            skipped.append({'step':step,'reason':'hair_anchor_mismatch'});continue
        base=int.from_bytes(rom[0xed6d:0xed70],'little');tile_data=rom[lorom_offset(base)+(meta['selector']-1)*32:][:32]
        pixels=decode_tile(tile_data,0);palette=recorded['palette'];hair_pixels={}
        for py in range(8):
            for px in range(8):
                value=pixels[py][7-px]
                if value and 0<=x+px<256 and 0<=y+py<224:hair_pixels[(x+px,y+py)]=ppu_color(cgram,128+palette*16+value)
        observed_hair=compose(oam,vram,cgram,ppu['obsel'],[f['hair_slot']])
        if hair_pixels!=observed_hair:
            skipped.append({'step':step,'reason':'hair_tile_mismatch'});continue
        current_palette=[list(ppu_color(cgram,128+palette*16+i)) for i in range(16)]
        if palette_rgb is None:palette_rgb=current_palette
        elif palette_rgb!=current_palette:
            skipped.append({'step':step,'reason':'palette_changed'});continue
        frames.append({'step':step,'descriptor':meta['descriptor'],'sheet_frame':index,'origin_x':anchor['origin_x'],
                       'origin_y':anchor['origin_y'],'hair_x':-meta['x']-4,'hair_y':meta['y']-4,
                       'selector':meta['selector'],'body_pixels':len(body_pixels),'hair_pixels':len(hair_pixels),'detail':detail})
    if not frames:raise ValueError('No exactly matched frames')
    if detail_output is not None:
        detail_output.parent.mkdir(parents=True,exist_ok=True)
        detail_output.write_text(json.dumps({'schema':'issd-dynamic-detail-local/v1','tiles':detail_tiles},separators=(',',':')),encoding='utf8')
    return {'schema':'issd-dynamic-hair-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'trace_sha256':hashlib.sha256((root/'hair-runtime.jsonl').read_bytes()).hexdigest(),
            'sheet_sha256':hashlib.sha256(sheet_path.read_bytes()).hexdigest(),
            'team':2,'kit':'home','motion':'walking','direction':4,'style':1,'palette':1,'palette_rgb':palette_rgb,
            'cell_width':direction['cell_width'],'cell_height':direction['cell_height'],'frames':frames,'skipped':skipped,
            'limitations':['One synthetic actor position, one style, one direction and one team palette.',
              'Exact match covers candidate pixels and captured frames; does not establish all runtime configurations.',
              'Current team sheets are converted from floor-expanded RGB to the PPU bit-replicated RGB.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('root',type=Path)
    p.add_argument('anchors',type=Path);p.add_argument('geometry',type=Path);p.add_argument('sheet',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--detail-output',type=Path);a=p.parse_args()
    result=audit(a.rom.read_bytes(),a.root,json.loads(a.anchors.read_text(encoding='utf8')),
                 json.loads(a.geometry.read_text(encoding='utf8')),a.sheet,a.detail_output)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Verified {len(result['frames'])} composed frames")
