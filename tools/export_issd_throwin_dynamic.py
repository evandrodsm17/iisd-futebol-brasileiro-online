"""Build local throw-in body compositions from audited OAM and ROM tiles."""
import argparse
import base64
import json
from pathlib import Path

from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive
from audit_issd_throwin_body import audit, actual
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_oam_pixels import compose, compare
from PIL import Image


def b64(data): return base64.b64encode(data).decode('ascii')


def recover_split_draw(root, rom, events, poses, frame):
    # One draw list is split across adjacent frame counters. Use its recorded
    # geometry only if the later mirror, PPU, ROM layout and screen all agree.
    if frame != 2267: raise ValueError('Unexpected split-draw frame')
    draw=[e for e in events if not e.get('type')]
    indices=[i for i,e in enumerate(draw) if e['frame']==frame-2 and e['object']==0x600]
    ball_indices=[i for i,e in enumerate(draw) if e['frame']==frame-2 and e['object']==0x400]
    geometries=[e for e in events if e.get('type')=='body_geometry' and e['frame']==frame-2 and e['object']==0x600]
    if len(indices)!=1 or len(ball_indices)!=1 or len(geometries)!=1:raise ValueError('Missing split-draw evidence')
    i,b=indices[0],ball_indices[0]
    if i+1>=len(draw) or b+1>=len(draw) or draw[i+1]['frame'] not in (frame-2,frame-1):raise ValueError('Unexpected split-draw continuation')
    g=geometries[0];capture=poses[frame];displayed=poses[frame+1]
    if g['source']!='rom88' or g['parts']!=rom_parts(rom,g['pose']) or (g['descriptor'],g['pose'],g['tile_base'])!=(capture['descriptor'],capture['pose'],capture['object_field_02']):raise ValueError('Split pose differs')
    trace=[json.loads(line) for line in (root/'trace.jsonl').read_text().splitlines() if line.strip()]
    actors=[]
    for f in (frame-1,frame):
        rows=[r for r in trace if r.get('frame')==f]
        if len(rows)!=1:raise ValueError('Missing split actor trace')
        players=[a for a in rows[0]['actors'] if a['address']==0x600]
        if len(players)!=1:raise ValueError('Missing split actor')
        actors.append(players[0])
    if any((a['x'],a['y'],a['descriptor'])!=(g['draw_x'],g['draw_y'],g['descriptor']) for a in actors) or actors[0]['direction']!=actors[1]['direction'] or g['draw_z']!=0:raise ValueError('Split actor moved')
    candidates=slots(draw[i]['stack'],draw[i+1]['stack']);ball=slots(draw[b]['stack'],draw[b+1]['stack'])
    parts=derive(g,g,capture['obsel'],candidates)
    mirror=(root/(capture['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
    ppu=(root/(displayed['stem']+'-ppu.bin')).read_bytes()
    if any(p!=actual(mirror,p,capture['obsel']) or p!=actual(ppu,p,capture['obsel']) for p in parts):raise ValueError('Split OAM mismatch')
    stem=displayed['stem'];pixels=compose(ppu,(root/(stem+'-vram.bin')).read_bytes(),(root/(stem+'-ppu-cgram.bin')).read_bytes(),displayed['obsel'],candidates+ball)
    with Image.open(root/(stem+'-screen.png')) as image: comparison=compare(pixels,image)
    if not comparison['candidate_pixels'] or comparison['nonmatching_pixels']:raise ValueError('Split screen mismatch')
    return g,parts


def export(analysis,rom_path,out,receipt=False,contested=False):
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
    cases=[(2,'throw-in-receiver-more/lower-A-Left',0x1500,2321,2364)] if contested else [(3,'throw-in-receiver-visual/lower-B-Right',0x900,2301,2344)] if receipt else [(4,'throw-in-body-directions/Down',0x600,2267,2286),(5,'throw-in-body-directions/Left',0x600,2267,2286),(3,'throw-in-body-directions/Right',0x600,2267,2286),(7,'throw-in-lower-directions/Left',0x600,2267,2286),(0,'throw-in-lower-directions/Up',0x600,2267,2286),(1,'throw-in-lower-directions/Right',0x600,2267,2286)]
    for direction,rel,actor_id,first,last in cases:
        root=analysis/rel;report=audit(root,rom_path,actor_id,True,True,True,True,contested)
        validated={x['prepared_frame']:x for x in report['frames']}
        poses={x['frame']:x for x in map(json.loads,(root/'slide-poses.jsonl').read_text().splitlines())}
        events=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()]
        frames=[];variants_cache={}
        for frame in range(first,last+1):
            split_recovered = frame not in validated
            if split_recovered:
                if rel not in ('throw-in-lower-directions/Up','throw-in-lower-directions/Right'):raise ValueError('Missing validated frame')
                g,parts=recover_split_draw(root,rom,events,poses,frame)
                record=poses[frame+1]
            else:
                item=validated[frame];record=poses[item['displayed_frame']]
                gs=[x for x in events if x.get('type')=='body_geometry' and x['frame']==frame-1 and x['object']==actor_id]
                if len(gs)!=1:raise ValueError('Missing geometry')
                g=gs[0];draw=[x for x in events if not x.get('type') and x['frame']==frame-1]
                ids=[i for i,x in enumerate(draw) if x['object']==actor_id]
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
            output={'descriptor':g['descriptor'],'ticks':1,'obsel':record['obsel'],'parts':parts,'tiles':tiles,'cgram':b64(cgram),'capture_method':'split-draw-verified' if split_recovered else 'direct'}
            if not receipt and not contested and frame < 2271:
                all_draw=[e for e in events if not e.get('type')]
                draw_frame=frame-2 if split_recovered else frame-1
                ball_indices=[i for i,e in enumerate(all_draw) if e['frame']==draw_frame and e['object']==0x400]
                if len(ball_indices)!=1 or ball_indices[0]+1>=len(all_draw):raise ValueError('Missing held-ball draw range')
                i=ball_indices[0];ball_slots=slots(all_draw[i]['stack'],all_draw[i+1]['stack'])
                body_slots=[part['slot'] for part in parts]
                if not ball_slots or set(ball_slots)&set(body_slots):raise ValueError('Invalid held-ball slots')
                stem=record['stem'];ppu=(root/(stem+'-ppu.bin')).read_bytes();vram=(root/(stem+'-vram.bin')).read_bytes()
                ball_pixels=compose(ppu,vram,cgram,record['obsel'],ball_slots)
                combined=compose(ppu,vram,cgram,record['obsel'],body_slots+ball_slots)
                with Image.open(root/(stem+'-screen.png')) as screen:comparison=compare(combined,screen)
                if not ball_pixels or comparison['nonmatching_pixels']:raise ValueError('Held ball and body do not match screen')
                left=min(x for x,y in ball_pixels);top=min(y for x,y in ball_pixels)
                right=max(x for x,y in ball_pixels);bottom=max(y for x,y in ball_pixels)
                image=Image.new('RGBA',(right-left+1,bottom-top+1))
                for (x,y),color in ball_pixels.items():image.putpixel((x-left,y-top),(*color,255))
                output['held_ball']={'x':left-g['draw_x'],'y':top-((g['draw_y']+g['draw_z'])&0xffff),
                                     'width':image.width,'height':image.height,'rgba':b64(image.tobytes()),
                                     'front':min(ball_slots)<min(body_slots)}
            main_bank,detail_bank=(1,5) if contested else (0,4)
            extra=[p for p in parts if (p['attr']>>1)&7==detail_bank]
            if any(((p['attr']>>1)&7) not in (main_bank,detail_bank) for p in parts):raise ValueError('Unexpected palette')
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
    data={'schema':'issd-contested-receipt-local/v1' if contested else 'issd-receipt-dynamic-local/v1' if receipt else 'issd-throwin-dynamic-local/v1','width':96,'height':96,'cycles':cycles,
          'ticks_per_second':60,'detail_pool':pool,'palette10':palette10.pop(),'team_palette':team_palette,
          'limitations':[('One captured receipt context' if receipt or contested else 'Six captured input cases')+' and partial timing; hair not independently validated.',
                         'Local ROM-derived graphics; do not distribute.']}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    return len(pool)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True,type=Path);p.add_argument('--rom',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    group=p.add_mutually_exclusive_group();group.add_argument('--receipt',action='store_true',help='export captured receipt');group.add_argument('--contested-receipt',action='store_true',help='export receipt with verified foreground occlusion');a=p.parse_args();print('Dynamic detail tiles:',export(a.analysis,a.rom,a.output,a.receipt,a.contested_receipt))
