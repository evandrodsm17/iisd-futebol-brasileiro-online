"""Export locally validated directional slide compositions and ROM detail variants."""
import argparse, base64, json
from pathlib import Path
from audit_issd_slide_directions import DIRECTIONS
from compare_issd_action_trials import load
from export_issd_slide_lab import export
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile


def run(args):
    rom=args.rom.read_bytes();pool=[];pool_index={};cycles={};counts={}
    # 8B:D061 loads team goalkeeper palettes via 828326 to OBJ C1..CB.
    # Index 10 is the tenth word and is identical for all 43 table entries.
    palette10=set()
    for team in range(43):
        pointer=int.from_bytes(rom[0x10326+team*2:0x10328+team*2],'little')
        offset=0x48000+pointer-0x8000
        if not 0x48000<=offset or offset+24>len(rom) or int.from_bytes(rom[offset:offset+2],'little')!=21:raise ValueError('Unexpected goalkeeper palette table')
        palette10.add(int.from_bytes(rom[offset+20:offset+22],'little'))
    if len(palette10)!=1:raise ValueError('Palette index 10 is not invariant')
    palette10=palette10.pop()
    # A4:920B -> 81:E7D8 -> 80:A4EF: four team colors at OBJ CC..CF.
    team_palette=[]
    for team in range(36):
        pointer=int.from_bytes(rom[0xe7d8+team*2:0xe7da+team*2],'little')
        offset=0x48000+pointer-0x8000
        if not 0x48000<=offset or offset+10>len(rom) or int.from_bytes(rom[offset:offset+2],'little')!=7:raise ValueError('Unexpected team detail palette')
        team_palette.append([int.from_bytes(rom[offset+2+i*2:offset+4+i*2],'little') for i in range(4)])
    for screen,name in enumerate(DIRECTIONS):
        root=args.analysis/('slide-upright-paired/A' if name=='UpRight' else 'slide-direction-paired/A/'+name)
        control=args.analysis/('slide-upright-paired/neutral' if name=='UpRight' else 'slide-direction-control-graphics/'+name)
        a=load(next(root.glob('issd-auto-probe-*.jsonl')))['samples'][480]['held_p1']
        n=load(next(control.glob('issd-auto-probe-*.jsonl')))['samples'][480]['held_p1']
        if a^n != 0x80: raise ValueError('Input control mismatch')
        data=export(root,control,args.rom,args.state,args.catalog,a,n)
        if any(f['ticks'] < 1 for f in data['frames']):
            print(name, 'omitted: action interrupted before full timing could be observed')
            continue
        geometries=[json.loads(line) for line in (root/'slide-draw.jsonl').read_text().splitlines() if line.strip()]
        candidate=0
        for frame in data['frames']:
            matches=[g for g in geometries if g.get('type')=='body_geometry' and g['object']==0x0f00 and g['descriptor']==frame['descriptor'] and 4275<=g['frame']<=4300]
            if not matches: raise ValueError('Missing captured actor')
            g=matches[0]
            captured=base64.b64decode(frame['cgram'])
            if int.from_bytes(captured[(128+64+10)*2:(128+64+11)*2],'little')!=palette10:raise ValueError('Captured palette index 10 mismatch')
            observed_team=g['uniform_selector']//2
            observed_colors=[int.from_bytes(captured[(128+64+i)*2:(128+65+i)*2],'little') for i in (13,14,15)]
            if observed_team>=36 or observed_colors!=team_palette[observed_team][1:]:raise ValueError('Captured team detail palette mismatch')
            extra=[part for part in frame['parts'] if (part['attr']>>1)&7==4]
            if any(((p['attr']>>1)&7) not in (0,4) for p in frame['parts']): raise ValueError('Unexpected palette')
            if not extra: continue
            if any(p['size']!=8 for p in extra): raise ValueError('Unexpected detail size')
            # The tile number is the actor's dynamic tile 23, not a pre-rendered sprite.
            addresses=set()
            for part in extra:
                bank=part['attr']&1
                if ((part['tile']-(g['tile_base']&255))&255)!=23: raise ValueError('Unexpected detail tile')
                base=((frame['obsel']&7)<<9)+((((frame['obsel']&0x18)+8)<<5) if bank else 0)
                addresses.add(((base+part['tile'])&2047)*32)
            if len(addresses)!=1: raise ValueError('Ambiguous detail tile address')
            frame['detail_address']=next(iter(addresses));variants=[]
            for team in range(36):
                for shirt in range(1,21):
                    actor={'type':g['actor_type'],'kit_variant':2*(shirt-1),'uniform_selector':2*team,'object_flags':g['object_flags']}
                    raw,meta=descriptor_tiles(rom,frame['descriptor'],actor)
                    indices={pixel for row in decode_tile(raw,23) for pixel in row if pixel}
                    if meta['detail_source'] is None or indices-{10,12,13,14,15}:
                        variants.append(None);continue
                    tile=raw[23*32:24*32];encoded=base64.b64encode(tile).decode('ascii')
                    if encoded not in pool_index:pool_index[encoded]=len(pool);pool.append(encoded)
                    variants.append(pool_index[encoded]);candidate+=1
            frame['detail_variants']=variants
        cycles[str(screen)]=data['frames'];counts[name]=candidate
    result={'schema':'issd-slide-directions-local/v1','width':96,'height':96,'cycles':cycles,'detail_pool':pool,'palette10':palette10,'team_palette':team_palette}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    print('directions:',len(cycles),'detail tiles:',len(pool),'safe variants:',counts)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);run(p.parse_args())
