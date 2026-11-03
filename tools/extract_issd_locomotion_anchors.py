"""Recover per-frame actor origins from the OAM inputs of team motion sheets."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from extract_issd_catalog import EXPECTED_MD5
from export_issd_team_motion import descriptors, renderer, trace, SCRIPTS


def extract(rom, rows, actor_id, assets=None):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    rom=rom[header:];r=renderer();lookup={}
    for row in rows:
        for actor in row.get('actors',[]):
            if actor['address']==actor_id:
                lookup.setdefault((actor['direction'],actor['descriptor']),actor)
    cycles={};checked=0
    for motion,script in SCRIPTS.items():
        cycles[motion]=[]
        for direction in range(8):
            raw=[]
            for desc in descriptors(rom,script,direction):
                actor=lookup.get((direction,desc))
                if actor is None:raise ValueError(f'Missing captured pose {motion}/{direction}/${desc:04X}')
                parts=r.normalise_parts(actor['parts'])
                if not parts:raise ValueError('Empty geometry')
                left=min(p['x'] for p in parts);top=min(p['y'] for p in parts)
                right=max(p['x']+p['size'] for p in parts);bottom=max(p['y']+p['size'] for p in parts)
                raw.append({'descriptor':desc,'left':left,'top':top,'width':right-left,'height':bottom-top})
            cell_width=max(x['width'] for x in raw)+4;cell_height=max(x['height'] for x in raw)+4
            frames=[]
            for item in raw:
                # Exporter centers the cropped body and aligns its bottom at cell_height - 2.
                frames.append({**item,'origin_x':(cell_width-item['width'])//2-item['left'],
                               'origin_y':cell_height-item['height']-2-item['top']})
            if assets:
                for team in range(36):
                    for kit in ('home','away'):
                        path=assets/f'{team:02d}'/kit/f'{motion}-{direction}.png'
                        with Image.open(path) as image:
                            if image.size!=(cell_width*len(frames),cell_height):raise ValueError(f'Sheet size mismatch: {path}')
                        checked+=1
            cycles[motion].append({'direction':direction,'cell_width':cell_width,'cell_height':cell_height,'frames':frames})
    return {'schema':'issd-locomotion-anchors/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'actor':actor_id,'sheets_dimensions_verified':checked,'cycles':cycles,
            'limitations':['Origins describe the current exported sheets, not independently validated auxiliary OAM positions.',
                           'Per-team palette, hidden pieces, and final hair placement still require same-frame validation.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--actor',type=lambda x:int(x,0),default=0x0d00);p.add_argument('--assets',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=extract(a.rom.read_bytes(),trace(a.trace),a.actor,a.assets)
    result['trace_sha256']=hashlib.sha256(a.trace.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Recovered {sum(len(d['frames']) for c in result['cycles'].values() for d in c)} frame origins; checked {result['sheets_dimensions_verified']} sheets")
