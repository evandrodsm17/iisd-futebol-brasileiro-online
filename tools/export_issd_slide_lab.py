"""Prepare a local, body-only slide preview from the audited replay."""
import argparse
import base64
import json
from pathlib import Path

from audit_issd_actor_oam_properties import derive
from audit_issd_slide_body_upload import audit
from analyze_issd_draw_trace import slots as draw_slots
from compare_issd_action_trials import load
from render_issd_descriptor_sprite import descriptor_tiles


def encode(value): return base64.b64encode(value).decode('ascii')


def export(root,control,rom_path,state,catalog):
    report=audit(root,control,rom_path,state,catalog)
    rom=rom_path.read_bytes()
    records=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()]
    captures={r['frame']:r for r in (json.loads(x) for x in (root/'slide-poses.jsonl').read_text().splitlines() if x.strip())}
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1: raise ValueError('Expected one replay trace')
    samples=load(paths[0])['samples']
    durations=[]
    for item in report['frames']:
        first=next(t for t in range(480,510) if samples[t]['frame']==item['displayed_frame']-1)
        end=first
        while end<510 and samples[end]['actor']['descriptor']==item['descriptor']: end+=1
        durations.append(end-first)
    frames=[]
    for item,duration in zip(report['frames'],durations):
        displayed=item['displayed_frame'];capture=captures[displayed]
        geometry=[r for r in records if r.get('type')=='body_geometry' and r['frame']==displayed-2 and r['object']==report['actor']]
        if len(geometry)!=1: raise ValueError('Missing validated geometry')
        g=geometry[0];draw=[r for r in records if not r.get('type') and r['frame']==displayed-2]
        indices=[i for i,r in enumerate(draw) if r.get('object')==report['actor']]
        if len(indices)!=1 or indices[0]+1>=len(draw): raise ValueError('Missing actor draw range')
        i=indices[0];slots=draw_slots(draw[i]['stack'],draw[i+1]['stack'])
        parts=derive(g,g,capture['obsel'],slots)
        for part in parts:
            part['x']+=48-g['draw_x'];part['y']+=60-((g['draw_y']+g['draw_z'])&0xffff)
            if not (0<=part['x']<96 and 0<=part['y']<96 and part['x']+part['size']<=96 and part['y']+part['size']<=96):
                raise ValueError('Piece outside preview cell')
        tile_data,_=descriptor_tiles(rom,item['descriptor']);base=g['tile_base']&255
        tiles=[]
        for bank,indices in item['used_relative_tiles'].items():
            base_address=((capture['obsel']&7)<<9)+((((capture['obsel']&0x18)+8)<<5) if int(bank) else 0)
            for index in indices:
                address=((base_address+((base+index)&255))&2047)*32
                tiles.append({'address':address,'data':encode(tile_data[index*32:(index+1)*32])})
        frames.append({'descriptor':item['descriptor'],'ticks':duration,'obsel':capture['obsel'],
                       'parts':parts,'tiles':tiles,'cgram':encode((root/(capture['stem']+'-ppu-cgram.bin')).read_bytes())})
    return {'schema':'issd-slide-lab-local/v1','width':96,'height':96,'frames':frames,
            'limitations':['Body only; auxiliary hair is not validated.',
                           'One captured actor, palette, direction, scenario and interrupted timing.',
                           'ROM-derived graphics; generate locally and do not distribute.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--rom',required=True,type=Path);p.add_argument('--state',required=True,type=Path);p.add_argument('--catalog',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();data=export(a.root,a.control,a.rom,a.state,a.catalog);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8');print('exported local preview:',len(data['frames']),'poses')
