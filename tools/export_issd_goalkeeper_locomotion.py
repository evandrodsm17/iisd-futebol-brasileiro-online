"""Export ROM keeper locomotion descriptors matched to observed geometry."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from export_issd_team_motion import descriptors,trace
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import decompress
from render_issd_descriptor_sprite import descriptor_tiles


def export(rom,trace_path):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];data,interleaved=decompress(rom,0x9888be)
    count=int.from_bytes(data[1:3],'little');start=3+data[0]
    if interleaved or len(data)!=start+count*4 or sum(data[3:start])!=count:raise ValueError('Unsupported goalkeeper geometry')
    poses={};cursor=0
    for length in data[3:start]:
        parts=[]
        for i in range(cursor,cursor+length):
            x,y,tile,attr=(data[start+count*j+i] for j in range(4))
            signed=lambda n:(n if n<128 else n-256)&0xffff
            parts.append({'dx':signed(x),'dy':signed(y),'tile':tile,'attr':attr&0xef,'large':bool(attr&0x10)})
        poses[0x4988+cursor*2]=parts;cursor+=length
    observed={}
    for row in trace(trace_path):
        for actor in row.get('actors',[]):
            if actor.get('animation_script')==0xe34a and actor.get('type')==1 and actor.get('parts'):
                offset=0x10000+(actor['descriptor']&0x7fff)
                if actor.get('pose')==int.from_bytes(rom[offset:offset+2],'little'):
                    observed.setdefault((actor['direction'],actor['descriptor']),actor)
    cycles=[];missing=[]
    for direction in range(8):
        sequence=descriptors(rom,0xe34a,direction);frames=[]
        for desc in sequence:
            actor=observed.get((direction,desc))
            if not actor:missing.append({'direction':direction,'descriptor':desc});frames.append(None);continue
            offset=0x10000+(desc&0x7fff);pose=int.from_bytes(rom[offset:offset+2],'little');parts=poses.get(pose)
            if not parts or len(parts)!=len(actor['parts']):raise ValueError(f'Unmatched keeper geometry {desc:04X}')
            def attr(raw,props):
                out=(raw&0xc1)^props
                if raw&0x20:out=out|2 if out&8 else (out&0xfb)|8
                return out
            props=[p for p in range(256) if bool(p&64)==bool(actor['object_flags']&64) and all(attr(a['attr'],p)==b['attr'] for a,b in zip(parts,actor['parts']))]
            if len(props)!=1:raise ValueError('Ambiguous keeper attributes')
            signed=lambda n:n if n<32768 else n-65536
            for p,o in zip(parts,actor['parts']):
                dx=signed(p['dx']);dy=signed(p['dy']);large=p['large']
                if props[0]&64:dx=-dx
                if (dx-(8 if large else 4),dy-(8 if large else 4),p['tile'],16 if large else 8)!=(o['x'],o['y'],o.get('geometry_tile',o['tile']),o['size']):raise ValueError(f'Keeper geometry mismatch {direction}/{desc:04X}')
            tiles,_=descriptor_tiles(rom,desc)
            frames.append({'descriptor':desc,'props':props[0],'parts':parts,'tiles':base64.b64encode(tiles).decode('ascii')})
        # A common box per direction preserves the observed relative origin.
        samples=[observed[(direction,d)] for d in sequence if (direction,d) in observed]
        left=min(p['x'] for s in samples for p in s['parts']);top=min(p['y'] for s in samples for p in s['parts'])
        right=max(p['x']+p['size'] for s in samples for p in s['parts']);bottom=max(p['y']+p['size'] for s in samples for p in s['parts'])
        for f in frames:
            if f:f.update({'origin_x':2-left,'origin_y':2-top})
        cycles.append({'direction':direction,'width':right-left+4,'height':bottom-top+4,'frames':frames})
    if len(missing)!=3 or any(x['direction']!=4 for x in missing):raise ValueError('Unexpected capture coverage')
    return {'schema':'issd-goalkeeper-locomotion-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'cycles':cycles,'missing':missing,
            'limitations':['OAM geometry from natural trace; no same-frame VRAM/CGRAM screenshot comparison.',
             'Goalkeeper palette from editor preview is provisional for gameplay.',
             'Three direction-4 frames have no observed geometry and must not be synthesized.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=export(a.rom.read_bytes(),a.trace);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,separators=(',',':')),encoding='utf8');print(f"Exported keeper data; {len(r['missing'])} frames pending")
