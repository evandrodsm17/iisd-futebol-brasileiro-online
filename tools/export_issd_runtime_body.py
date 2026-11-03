"""Export local descriptor rows and observed locomotion context for web runtime."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from export_issd_team_motion import trace,descriptors,SCRIPTS
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def export(rom,geometry,anchors,trace_path):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];sha=hashlib.sha256(rom).hexdigest()
    if geometry['rom_sha256']!=sha or anchors['rom_sha256']!=sha:raise ValueError('ROM evidence mismatch')
    observed={}
    for sample in trace(trace_path):
        for actor in sample.get('actors',[]):
            if actor['address']==0x0d00:observed.setdefault((actor['direction'],actor['descriptor']),actor)
    cycles={}
    for motion,script in SCRIPTS.items():
        cycles[motion]=[]
        for direction in range(8):
            anchor=anchors['cycles'][motion][direction];frames=[]
            for idx,desc in enumerate(descriptors(rom,script,direction)):
                actor=observed[(direction,desc)];parts=geometry['poses'][str(desc)]['parts'];reference=actor['parts']
                def attr(raw,props):
                    out=(raw&0xc1)^props
                    if raw&0x20:out=out|2 if out&8 else (out&0xfb)|8
                    return out
                candidates=[p for p in range(256) if bool(p&64)==bool(actor['object_flags']&64) and
                            len(parts)==len(reference) and all(attr(x['attr'],p)==y['attr'] for x,y in zip(parts,reference))]
                if len(candidates)!=1:raise ValueError(f'Ambiguous actor properties {motion}/{direction}/{desc:04X}')
                tiles,_=descriptor_tiles(rom,desc,actor)
                frames.append({'descriptor':desc,'props':candidates[0],'origin_x':anchor['frames'][idx]['origin_x'],
                               'origin_y':anchor['frames'][idx]['origin_y'],'parts':parts,
                               'tiles':base64.b64encode(tiles).decode('ascii')})
            cycles[motion].append({'width':anchor['cell_width'],'height':anchor['cell_height'],'frames':frames})
    return {'schema':'issd-runtime-body-local/v1','rom_sha256':sha,'cycles':cycles,
            'limitations':['Reproduces the existing exported body sheets and their single-palette behavior.',
             'Actor context is from one historical trace; individual hair and secondary palette are not generalized.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('geometry',type=Path);p.add_argument('anchors',type=Path);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=export(a.rom.read_bytes(),json.loads(a.geometry.read_text(encoding='utf8')),json.loads(a.anchors.read_text(encoding='utf8')),a.trace)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,separators=(',',':')),encoding='utf8');print('Exported runtime locomotion data locally')
