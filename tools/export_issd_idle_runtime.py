"""Export locally observed idle OAM parts and indexed VRAM pixels."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_oam_composite import decode_tile


def export(rom,trace_path,scripts):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];rows=[json.loads(line) for line in trace_path.read_text(encoding='utf8').splitlines() if line.strip()]
    observed={}
    for row in rows:
        a=row['actor'];key=(a['animation_script'],a['direction'],a['descriptor'])
        if a['animation_script'] in (0xd320,0xd6db) and a['pose']<0x8000 and a['parts'] and all(abs(p[axis])<=128 for p in a['parts'] for axis in ('x','y')):observed.setdefault(key,row)
    cycles={}
    for name,script in [('idle',0xd320),('idle_with_ball',0xd6db)]:
        cycles[name]=[]
        for direction in range(8):
            descs=scripts['actions'][name]['directions'][direction]['descriptors'];available=[]
            for desc in dict.fromkeys(descs):
                row=observed.get((script,direction,desc))
                if not row:continue
                vram=Path(row['vram']).read_bytes();cgram=bytes.fromhex(Path(row['cgram']).read_text(encoding='utf8'))
                if len(vram)!=65536 or len(cgram)!=512:raise ValueError('Missing matching VRAM/CGRAM')
                parts=[]
                for p in row['actor']['parts']:
                    size=p['size'];attr=p['attr'];base=((row['obsel']&7)<<9)+(((((row['obsel']&24)+8)<<5)) if attr&1 else 0)
                    pixels=bytearray()
                    for y in range(size):
                        for x in range(size):
                            sx=size-1-x if attr&64 else x;sy=size-1-y if attr&128 else y
                            tile=(p['tile']&0xf0)|((p['tile']+(sx>>3))&15)
                            pixels.append(decode_tile(vram,base+tile+16*(sy>>3))[sy&7][sx&7])
                    parts.append({'x':p['x'],'y':p['y'],'size':size,'palette':(attr>>1)&7,'pixels':base64.b64encode(pixels).decode('ascii')})
                available.append({'descriptor':desc,'parts':parts,'cgram':base64.b64encode(cgram).decode('ascii')})
            if not available:raise ValueError(f'Missing observed {name} direction {direction}')
            if name=='idle' and {f['descriptor'] for f in available}!=set(descs):raise ValueError(f'Incomplete idle direction {direction}')
            left=min(p['x'] for f in available for p in f['parts']);top=min(p['y'] for f in available for p in f['parts'])
            right=max(p['x']+p['size'] for f in available for p in f['parts']);bottom=max(p['y']+p['size'] for f in available for p in f['parts'])
            cycles[name].append({'direction':direction,'sequence':descs,'left':left,'top':top,'width':right-left,'height':bottom-top,'frames':available})
    timing=list(rom[0x16414:0x16418])
    if timing!=[24,6,24,6]:raise ValueError('Unexpected $82:E414 timing table')
    return {'schema':'issd-idle-runtime-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'cycles':cycles,'idle_durations':timing,
            'limitations':['Captured OAM/VRAM-derived indexed graphics; no per-player hair layer.',
             'With-ball cycle has incomplete capture coverage; only observed poses may be shown.',
             'Team palette override follows existing provisional single-palette behavior.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path);p.add_argument('scripts',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=export(a.rom.read_bytes(),a.trace,json.loads(a.scripts.read_text(encoding='utf8')))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':')),encoding='utf8');print('Exported observed idle poses for eight directions')
