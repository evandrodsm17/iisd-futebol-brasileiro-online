"""Export team uniforms for captured fall and continuation directions."""
import argparse,base64,hashlib,json
from pathlib import Path
from export_issd_fall_lab import export,read
from export_issd_fall_recovery import export as export_recovery
from export_issd_jump_directions import palettes
from render_issd_descriptor_sprite import descriptor_tiles
from render_issd_oam_composite import decode_tile

CASES=[
 ('5','slide',Path('slide-fall-graphics'),{},{}),
 ('1','upright',Path('fall-directions/UpRight'),{'trigger':420,'start_elapsed':425,'direction':7,'descriptors':(0xb58f,0xb598,0xb4ff),'action_input':0x80,'neutral_input':0,'expected_link':0xe00},
  {'trigger':420,'first_frame':4256,'direction':7,'descriptor':0xafb9,'expected_state':0x340,'expected_script':0xd94d,'action_input':0x80,'neutral_input':0,'verify_exit':False}),
 ('3','downright',Path('fall-directions/DownRight'),{'trigger':420,'start_elapsed':432,'direction':1,'descriptors':(0xb5b3,0xb5bc,0xb4ed),'action_input':0x80,'neutral_input':0,'expected_link':0},
  {'trigger':420,'first_frame':4263,'direction':1,'descriptor':0xb2ec,'expected_state':0x2f8,'expected_script':0xdb5b,'action_input':0x80,'neutral_input':0,'verify_exit':False}),
 ('6','left',Path('fall-directions/Left'),{'trigger':420,'start_elapsed':425,'direction':4,'descriptors':(0xb5a1,0xb5aa,0xb4f6),'action_input':0x80,'neutral_input':0,'expected_link':0xf00},
  {'trigger':420,'first_frame':4256,'direction':4,'descriptor':0xc249,'expected_state':0x350,'expected_script':0xe214,'action_input':0x80,'neutral_input':0,'verify_exit':False}),
 ('2','right',Path('fall-directions/Right'),{'trigger':420,'start_elapsed':425,'direction':0,'descriptors':(0xb5a1,0xb5aa,0xb4f6),'action_input':0x80,'neutral_input':0,'expected_link':0xe00},
  {'trigger':420,'first_frame':4256,'direction':0,'descriptor':0xafef,'expected_state':0x340,'expected_script':0xd94d,'action_input':0x80,'neutral_input':0,'verify_exit':False}),
 ('7','upleft',Path('fall-directions/UpLeft'),{'trigger':420,'start_elapsed':425,'direction':5,'descriptors':(0xb58f,0xb598,0xb4ff),'action_input':0x80,'neutral_input':0,'expected_link':0},
  {'trigger':420,'first_frame':4256,'direction':5,'descriptor':0xb280,'expected_state':0x2f8,'expected_script':0xdb5b,'action_input':0x80,'neutral_input':0,'verify_exit':False}),
]

def build(args):
    rom=args.rom.read_bytes();palette10,team_palette=palettes(rom);pool=[];index={};cycles={};reports={}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for screen,name,folder,opts,continuation_opts in CASES:
        root=args.analysis/folder/'A';control=args.analysis/folder/'NEUTRAL'
        local,report=export(root,control,args.rom,args.state,**opts)
        continuation,continuation_report=export_recovery(root,control,args.rom,args.state,**continuation_opts)
        suffix='' if name=='slide' else '-'+name
        (args.output.parent/('fall'+suffix+'.json')).write_text(json.dumps(local,separators=(',',':')),encoding='utf8')
        (args.output.parent/('fall-recovery'+suffix+'.json')).write_text(json.dumps(continuation,separators=(',',':')),encoding='utf8')
        local['frames'].extend(continuation['frames']);items=report['frames']+continuation_report['frames']
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
        cycles[screen]=local['frames'];reports[name]={'fall':report,'continuation':continuation_report}
    result={'schema':'issd-fall-dynamic-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'width':96,'height':96,'ticks_per_second':60,'cycles':cycles,'detail_pool':pool,'palette10':palette10,'team_palette':team_palette,
            'limitations':['Six captured directions and contexts; others are unavailable.','Only slide case is proven as a tackle; other cases are defensive actions.','Team and shirt variants are ROM-derived and are not individually captured.','Hair and continuation beyond the first five frames are not included.']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    args.evidence.write_text(json.dumps(reports['slide']['fall'],indent=2)+'\n',encoding='utf8')
    args.recovery_evidence.write_text(json.dumps(reports['slide']['continuation'],indent=2)+'\n',encoding='utf8')
    args.direction_evidence.write_text(json.dumps({'schema':'issd-fall-direction-evidence/v1','directions':reports},indent=2)+'\n',encoding='utf8')
    print('OK:',len(cycles),'directions,',len(pool),'detail tiles')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--recovery-evidence',type=Path,required=True);p.add_argument('--direction-evidence',type=Path,default=Path('docs/issd-fall-direction-evidence.json'));build(p.parse_args())
