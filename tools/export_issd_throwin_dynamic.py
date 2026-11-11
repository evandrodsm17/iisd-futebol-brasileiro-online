"""Build local throw-in body compositions from audited OAM and ROM tiles."""
import argparse
import base64
import json
from pathlib import Path

from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive
from audit_issd_throwin_body import audit
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile


def b64(data): return base64.b64encode(data).decode('ascii')


def export(analysis,rom_path,out):
    rom=rom_path.read_bytes();pool=[];pool_index={};cycles={}
    palette10=set()
    for team in range(43):
        ptr=int.from_bytes(rom[0x10326+team*2:0x10328+team*2],'little');offset=0x48000+ptr-0x8000
        if not 0x48000<=offset or offset+24>len(rom) or int.from_bytes(rom[offset:offset+2],'little')!=21:raise ValueError('Unexpected goalkeeper palette')
        palette10.add(int.from_bytes(rom[offset+20:offset+22],'little'))
    if len(palette10)!=1:raise ValueError('Palette color not invariant')
    team_palette=[]
    for team in range(36):
        ptr=int.from_bytes(rom[0xe7d8+team*2:0xe7da+team*2],'little');offset=0x48000+ptr-0x8000
        if not 0x48000<=offset or offset+10>len(rom) or int.from_bytes(rom[offset:offset+2],'little')!=7:raise ValueError('Unexpected detail palette')
        team_palette.append([int.from_bytes(rom[offset+2+i*2:offset+4+i*2],'little') for i in range(4)])
    for direction,rel in [(4,'throw-in-body-directions/Down'),(0,'throw-in-lower-directions/Left')]:
        root=analysis/rel;report=audit(root,rom_path,0x600,True,True,True,True)
        validated={x['prepared_frame']:x for x in report['frames']}
        poses={x['frame']:x for x in map(json.loads,(root/'slide-poses.jsonl').read_text().splitlines())}
        events=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()]
        frames=[];variants_cache={}
        for frame in range(2267,2287):
            if frame not in validated:raise ValueError('Missing validated frame')
            item=validated[frame];record=poses[item['displayed_frame']]
            gs=[x for x in events if x.get('type')=='body_geometry' and x['frame']==frame-1 and x['object']==0x600]
            if len(gs)!=1:raise ValueError('Missing geometry')
            g=gs[0];draw=[x for x in events if not x.get('type') and x['frame']==frame-1]
            ids=[i for i,x in enumerate(draw) if x['object']==0x600]
            if len(ids)!=1 or ids[0]+1>=len(draw):raise ValueError('Missing draw range')
            i=ids[0];parts=derive(g,g,record['obsel'],slots(draw[i]['stack'],draw[i+1]['stack']))
            for part in parts:
                part['x']+=48-g['draw_x'];part['y']+=60-((g['draw_y']+g['draw_z'])&0xffff)
                if part['x']<0 or part['y']<0 or part['x']+part['size']>96 or part['y']+part['size']>96:raise ValueError('Piece outside canvas')
            actor={'type':g['actor_type'],'kit_variant':g['kit_variant'],'uniform_selector':g['uniform_selector'],'object_flags':g['object_flags']}
            source,_=descriptor_tiles(rom,g['descriptor'],actor);base=g['tile_base']&255
            captured=(root/(record['stem']+'-vram.bin')).read_bytes();used={};tiles=[]
            for part in parts:
                bank=part['attr']&1
                for y in range(part['size']//8):
                    for x in range(part['size']//8):
                        tile=(((part['tile']&0xf0)|((part['tile']+x)&15))+16*y)&255;relative=(tile-base)&255
                        address=((((record['obsel']&7)<<9)+((((record['obsel']&0x18)+8)<<5) if bank else 0)+tile)&2047)*32
                        chunk=source[relative*32:relative*32+32]
                        if len(chunk)!=32 or chunk!=captured[address:address+32]:raise ValueError(f'ROM tile mismatch: {frame}/{relative}')
                        used[address]=chunk
            tiles=[{'address':a,'data':b64(v)} for a,v in sorted(used.items())]
            cgram=(root/(record['stem']+'-ppu-cgram.bin')).read_bytes()
            output={'descriptor':g['descriptor'],'ticks':1,'obsel':record['obsel'],'parts':parts,'tiles':tiles,'cgram':b64(cgram)}
            extra=[p for p in parts if (p['attr']>>1)&7==4]
            if any(((p['attr']>>1)&7) not in (0,4) for p in parts):raise ValueError('Unexpected palette')
            if extra:
                addresses=set()
                for p in extra:
                    if p['size']!=8 or ((p['tile']-base)&255)!=23:raise ValueError('Unexpected detail tile')
                    tilebase=((record['obsel']&7)<<9)+((((record['obsel']&0x18)+8)<<5) if p['attr']&1 else 0)
                    addresses.add(((tilebase+p['tile'])&2047)*32)
                if len(addresses)!=1:raise ValueError('Ambiguous detail tile')
                output['detail_address']=next(iter(addresses));key=(g['descriptor'],g['actor_type'],g['object_flags'])
                if key not in variants_cache:
                    variants=[]
                    for team in range(36):
                        for shirt in range(1,21):
                            ctx={'type':g['actor_type'],'kit_variant':2*(shirt-1),'uniform_selector':2*team,'object_flags':g['object_flags']}
                            raw,meta=descriptor_tiles(rom,g['descriptor'],ctx)
                            indices={pixel for row in decode_tile(raw,23) for pixel in row if pixel}
                            if meta['detail_source'] is None or indices-{10,12,13,14,15}:variants.append(None);continue
                            encoded=b64(raw[23*32:24*32])
                            if encoded not in pool_index:pool_index[encoded]=len(pool);pool.append(encoded)
                            variants.append(pool_index[encoded])
                    variants_cache[key]=variants
                output['detail_variants']=variants_cache[key]
            frames.append(output)
        cycles[str(direction)]=frames
    data={'schema':'issd-throwin-dynamic-local/v1','width':96,'height':96,'cycles':cycles,
          'detail_pool':pool,'palette10':palette10.pop(),'team_palette':team_palette,
          'limitations':['Two captured orientations and partial timing; hair not independently validated.',
                         'Local ROM-derived graphics; do not distribute.']}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    return len(pool)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True,type=Path);p.add_argument('--rom',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print('Dynamic detail tiles:',export(a.analysis,a.rom,a.output))
