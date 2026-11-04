"""Audit ROM body uploads and auxiliary-hook coverage in a slide replay."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issd_action_palettes import matches, palette_hex
from audit_issd_actor_oam_properties import derive
from audit_issd_slide_timing_geometry import audit as audit_timing
from compare_issd_oam_pixels import compose
from render_issd_descriptor_sprite import descriptor_tiles


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, control, rom_path, state, catalog_path, action_input=0x80, neutral_input=0):
    timing=audit_timing(root,control,rom_path,state,action_input,neutral_input)
    rom=rom_path.read_bytes();teams=json.loads(catalog_path.read_text(encoding='utf-8'))['teams']
    draw_path=root/'slide-draw.jsonl';events=[json.loads(line) for line in draw_path.read_text().splitlines() if line.strip()]
    poses={r['frame']:r for r in (json.loads(line) for line in (root/'slide-poses.jsonl').read_text().splitlines() if line.strip())}
    auxiliary=[r for r in events if r.get('type')=='aux_execution']
    target=timing['actor'];target_aux=[r for r in auxiliary if r['parent_y']==target or r['context_parent']==target]
    if not auxiliary: raise ValueError('No auxiliary positive-control calls observed')
    frames=[]
    for item in timing['frames']:
        geometry=[r for r in events if r.get('type')=='body_geometry' and r['frame']==item['draw_frame'] and r['object']==target]
        if len(geometry)!=1: raise ValueError('Missing body geometry')
        geometry=geometry[0];record=poses[item['displayed_frame']];parts=derive(geometry,geometry,record['obsel'],item['slots'])
        oam=(root/(record['stem']+'-ppu.bin')).read_bytes();vram=(root/(record['stem']+'-vram.bin')).read_bytes()
        cgram=(root/(record['stem']+'-ppu-cgram.bin')).read_bytes();actor={key:geometry[field] for key,field in [('type','actor_type'),('kit_variant','kit_variant'),('uniform_selector','uniform_selector'),('object_flags','object_flags')]} if 'actor_type' in geometry else None
        source,meta=descriptor_tiles(rom,item['descriptor'],actor)
        if meta['pose']!=f"${geometry['pose']:04X}": raise ValueError('Descriptor pose mismatch')
        base=geometry['tile_base']&255;used={}
        for part in parts:
            bank=part['attr']&1
            for y in range(part['size']//8):
                for x in range(part['size']//8):
                    tile=(((part['tile']&0xf0)|((part['tile']+x)&15))+16*y)&255
                    used.setdefault(bank,set()).add((tile-base)&255)
        for bank,indices in used.items():
            tile_base=((record['obsel']&7)<<9)+((((record['obsel']&0x18)+8)<<5) if bank else 0)
            for tile in indices:
                address=((tile_base+((base+tile)&255))&2047)*32
                if tile*32+32>len(source) or source[tile*32:tile*32+32]!=vram[address:address+32]:
                    raise ValueError(f"ROM tile mismatch for {item['descriptor']:04X}/{tile}")
        banks=sorted({(part['attr']>>1)&7 for part in parts})
        pixels=compose(oam,vram,cgram,record['obsel'],item['slots'])
        if len(pixels)!=item['candidate_pixels']: raise ValueError('Candidate pixels changed')
        frames.append({'descriptor':item['descriptor'],'displayed_frame':item['displayed_frame'],
                       'rom_graphics_source':meta['graphics_source'],'detail_selector':meta['detail'],
                       'auxiliary_enable':meta['auxiliary_enable'],'auxiliary_selector':meta['auxiliary_selector'],
                       'used_relative_tiles':{str(bank):sorted(indices) for bank,indices in used.items()},
                       'all_used_tiles_match_rom':True,'candidate_pixels':len(pixels),
                       'palettes':[{'bank':bank,'catalog_matches':matches(palette_hex(cgram,bank),teams)} for bank in banks]})
    return {'schema':'issd-slide-body-upload/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'catalog_sha256':sha(catalog_path),'draw_trace_sha256':sha(draw_path),'actor':target,
            'baseline_samples':timing['baseline_samples'],'frames':frames,
            'auxiliary_probe':{'observed_calls_all_actors':len(auxiliary),
                               'calls_referencing_target':len(target_aux),
                               'first_frame':min(r['frame'] for r in auxiliary),
                               'last_frame':max(r['frame'] for r in auxiliary)},
            'limitations':['Exact tile comparison covers the body pieces in this one replay and direction.',
                           'A catalog palette match does not itself prove actor identity.',
                           'No target auxiliary hook calls does not prove hair is absent or never rendered elsewhere.',
                           'Captured OAM palette and actor context are not generalized to other teams or appearances.',
                           'Control-screen overlays and temporal correspondence retain the timing audit limitations.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.control,a.rom,a.state,a.catalog);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('poses:',len(r['frames']),'auxiliary calls:',r['auxiliary_probe']['observed_calls_all_actors'],'target:',r['auxiliary_probe']['calls_referencing_target'])
