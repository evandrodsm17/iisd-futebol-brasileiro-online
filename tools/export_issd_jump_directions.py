"""Export ROM-composed uniform variants for validated jump captures."""
import argparse,base64,hashlib,json
from pathlib import Path
from export_issd_jump_lab import export,read
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile

CASES=[('6','side',Path('slide-jump-graphics'),426,4,[0xbcd6,0xbcdf,0xbce8],False),
       ('0','up',Path('jump-directions/Up'),430,6,[0xbca0,0xbca9,0xbcb2],False),
       ('3','downright',Path('jump-directions/DownRight'),425,1,[0xbcf1,0xbcfa,0xbd03],True),
       ('4','down',Path('jump-directions/Down'),425,2,[0xbd0c,0xbd15,0xbd1e],True)]

def palettes(rom):
    values=[]
    for i in range(43):
        ptr=int.from_bytes(rom[0x10326+2*i:0x10328+2*i],'little');p=0x48000+ptr-0x8000
        if p<0x48000 or p+24>len(rom) or int.from_bytes(rom[p:p+2],'little')!=21:raise ValueError('Unexpected goalkeeper palette')
        values.append(int.from_bytes(rom[p+20:p+22],'little'))
    if len(set(values))!=1:raise ValueError('Color 10 not invariant')
    teams=[]
    for i in range(36):
        ptr=int.from_bytes(rom[0xe7d8+2*i:0xe7da+2*i],'little');p=0x48000+ptr-0x8000
        if p<0x48000 or p+10>len(rom) or int.from_bytes(rom[p:p+2],'little')!=7:raise ValueError('Unexpected team palette')
        teams.append([int.from_bytes(rom[p+2+2*j:p+4+2*j],'little') for j in range(4)])
    return values[0],teams

def build(args):
    rom=args.rom.read_bytes();palette10,team_palette=palettes(rom);pool=[];index={};cycles={};reports={}
    for screen,name,folder,start,direction,descriptors,occlusion in CASES:
        root=args.analysis/folder/'A';control=args.analysis/folder/'NEUTRAL'
        local,report=export(root,control,args.rom,args.state,start,descriptors,direction,occlusion)
        geometries=read(root/'slide-draw.jsonl');variant_cache={}
        for frame,item in zip(local['frames'],report['frames']):
            geometry=next(g for g in geometries if g.get('type')=='body_geometry' and g['frame']==item['prepared_frame']-1 and g['object']==0x1900)
            extras=[part for part in frame['parts'] if ((part['attr']>>1)&7)==5]
            if any(((part['attr']>>1)&7) not in (1,5) for part in frame['parts']):raise ValueError('Unexpected palette')
            if not extras:continue
            if any(p['size']!=8 or ((p['tile']-(geometry['tile_base']&255))&255)!=23 for p in extras):raise ValueError('Unexpected detail geometry')
            addresses={((((frame['obsel']&7)<<9)+((((frame['obsel']&0x18)+8)<<5) if p['attr']&1 else 0)+p['tile'])&2047)*32 for p in extras}
            if len(addresses)!=1:raise ValueError('Unexpected detail addresses')
            frame['detail_address']=next(iter(addresses));key=(frame['descriptor'],geometry['object_flags'])
            if key not in variant_cache:
                variants=[]
                for team in range(36):
                    for shirt in range(1,21):
                        actor={'type':geometry['actor_type'],'kit_variant':(shirt-1)*2,'uniform_selector':team*2,'object_flags':geometry['object_flags']}
                        raw,meta=descriptor_tiles(rom,frame['descriptor'],actor);values={v for row in decode_tile(raw,23) for v in row if v}
                        if meta['detail_source'] is None or values-{10,12,13,14,15}:variants.append(None);continue
                        tile=base64.b64encode(raw[23*32:24*32]).decode('ascii')
                        if tile not in index:index[tile]=len(pool);pool.append(tile)
                        variants.append(index[tile])
                variant_cache[key]=variants
            frame['detail_variants']=variant_cache[key]
        cycles[screen]=local['frames'];reports[name]=report
    result={'schema':'issd-jump-directions-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'width':96,'height':96,'ticks_per_second':60,'cycles':cycles,'detail_pool':pool,'palette10':palette10,'team_palette':team_palette,
            'limitations':['Four captured directions for one actor; other directions are unavailable.','Team and shirt variants derive from ROM tables; individual matches are not captured.','Hair layer is not validated.']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    args.evidence.write_text(json.dumps({'schema':'issd-jump-directions-evidence/v1','directions':reports},indent=2)+'\n',encoding='utf8')
    print('OK:',len(cycles),'directions,',len(pool),'distinct detail tiles')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);build(p.parse_args())
