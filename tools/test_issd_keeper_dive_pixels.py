"""Compare the browser compositor against the PPU for each captured dive pose."""
import argparse
import base64
import json
import subprocess
from pathlib import Path
from compare_issd_oam_pixels import compose


def verify(root,asset,evidence):
    report=json.loads(evidence.read_text(encoding='utf8'))
    result=subprocess.run(['node','tools/render_issd_keeper_dive_test.mjs',str(asset)],capture_output=True,text=True,check=True)
    frames=json.loads(result.stdout)
    captures={x['frame']:x for x in map(json.loads,(root/'slide-poses.jsonl').read_text(encoding='utf8').splitlines())}
    geometry=[x for x in map(json.loads,(root/'slide-draw.jsonl').read_text(encoding='utf8').splitlines()) if x.get('type')=='body_geometry' and x['object']==0x500]
    if len(frames)!=3 or len(report['frames'])!=3:raise ValueError('Unexpected frame count')
    for record,encoded in zip(report['frames'],frames):
        rgba=base64.b64decode(encoded,validate=True);capture=captures[record['displayed_frame']];g=next(x for x in geometry if x['frame']==record['prepared_frame']-1);stem=capture['stem']
        if len(rgba)!=96*96*4:raise ValueError('Invalid frame dimensions')
        pixels=compose((root/(stem+'-ppu.bin')).read_bytes(),(root/(stem+'-vram.bin')).read_bytes(),(root/(stem+'-ppu-cgram.bin')).read_bytes(),capture['obsel'],record['slots'])
        expected={(x+48-g['draw_x'],y+68-g['draw_y']-g['draw_z']):color for (x,y),color in pixels.items()}
        if any(not (0<=x<96 and 0<=y<96) for x,y in expected):raise ValueError('Pixel outside frame')
        for y in range(96):
            for x in range(96):
                pos=(y*96+x)*4;actual=rgba[pos:pos+4];rgb=expected.get((x,y))
                if rgb is None and actual[3]:raise ValueError('Unexpected opaque pixel')
                if rgb is not None and (actual[3]!=255 or any(abs(actual[i]-rgb[i])>1 for i in range(3))):raise ValueError(f'Pixel mismatch {record["descriptor"]:04X} ({x},{y})')
    return len(frames)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--asset',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    print('OK:',verify(a.root,a.asset,a.evidence),'browser frames match the captured PPU')
