"""Export ROM-composed uniforms for one validated fall capture."""
import argparse,base64,hashlib,json
from pathlib import Path
from export_issd_fall_lab import export,read
from export_issd_fall_recovery import export as export_recovery
from export_issd_jump_directions import palettes
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile

def build(args):
    rom=args.rom.read_bytes();palette10,team_palette=palettes(rom);pool=[];index={}
    root=args.analysis/'slide-fall-graphics/A';control=args.analysis/'slide-fall-graphics/NEUTRAL'
    local,report=export(root,control,args.rom,args.state);recovery,recovery_report=export_recovery(root,control,args.rom,args.state)
    local['frames'].extend(recovery['frames']);items=report['frames']+recovery_report['frames']
    geometries=read(root/'slide-draw.jsonl');variant_cache={}
    for frame,item in zip(local['frames'],items):
        g=next(x for x in geometries if x.get('type')=='body_geometry' and x['frame']==item['prepared_frame']-1 and x['object']==0x1900)
        extras=[p for p in frame['parts'] if ((p['attr']>>1)&7)==5]
        if any(((p['attr']>>1)&7) not in (1,5) for p in frame['parts']):raise ValueError('Unexpected palette')
        if not extras:continue
        if any(p['size']!=8 or ((p['tile']-(g['tile_base']&255))&255)!=23 for p in extras):raise ValueError('Unexpected detail geometry')
        addresses={((((frame['obsel']&7)<<9)+((((frame['obsel']&0x18)+8)<<5) if p['attr']&1 else 0)+p['tile'])&2047)*32 for p in extras}
        if len(addresses)!=1:raise ValueError('Unexpected detail addresses')
        frame['detail_address']=next(iter(addresses));key=(frame['descriptor'],g['object_flags'])
        if key not in variant_cache:
            variants=[]
            for team in range(36):
                for shirt in range(1,21):
                    actor={'type':g['actor_type'],'kit_variant':2*(shirt-1),'uniform_selector':2*team,'object_flags':g['object_flags']}
                    raw,meta=descriptor_tiles(rom,frame['descriptor'],actor);colors={v for row in decode_tile(raw,23) for v in row if v}
                    if meta['detail_source'] is None or colors-{10,12,13,14,15}:variants.append(None);continue
                    tile=base64.b64encode(raw[23*32:24*32]).decode('ascii')
                    if tile not in index:index[tile]=len(pool);pool.append(tile)
                    variants.append(index[tile])
            variant_cache[key]=variants
        frame['detail_variants']=variant_cache[key]
    result={'schema':'issd-fall-dynamic-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'width':96,'height':96,'ticks_per_second':60,'cycles':{'5':local['frames']},'detail_pool':pool,'palette10':palette10,'team_palette':team_palette,
            'limitations':['One captured direction; others are unavailable.','Team and shirt variants are ROM-derived and are not individually captured.','Hair and recovery beyond the initial five frames are not included.']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    args.evidence.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    args.recovery_evidence.write_text(json.dumps(recovery_report,indent=2)+'\n',encoding='utf8');print('OK:',len(local['frames']),'frames and',len(pool),'detail tiles')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--recovery-evidence',type=Path,required=True);build(p.parse_args())
