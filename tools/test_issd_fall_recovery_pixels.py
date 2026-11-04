"""Compare browser fall-compositor output with captured PPU pixels."""
import argparse,base64,json,subprocess
from pathlib import Path
from compare_issd_oam_pixels import compose


def verify(root,asset,evidence):
    report=json.loads(evidence.read_text(encoding='utf8'));records=report['frames']
    js=subprocess.run(['node','tools/render_issd_fall_recovery_test.mjs',str(asset)],capture_output=True,text=True,check=True)
    frames=json.loads(js.stdout);captures={r['frame']:r for r in map(json.loads,(root/'slide-poses.jsonl').read_text().splitlines())}
    geom=[r for r in map(json.loads,(root/'slide-draw.jsonl').read_text().splitlines()) if r.get('type')=='body_geometry' and r['object']==report['actor']]
    if len(records)!=5 or len(frames)!=5:raise ValueError('Unexpected frame count')
    for rec,encoded in zip(records,frames):
        frame=base64.b64decode(encoded,validate=True)
        if len(frame)!=96*96*4:raise ValueError('Invalid browser frame')
        capture=captures[rec['displayed_frame']];g=next(r for r in geom if r['frame']==rec['prepared_frame']-1);stem=capture['stem']
        original=compose((root/(stem+'-ppu.bin')).read_bytes(),(root/(stem+'-vram.bin')).read_bytes(),(root/(stem+'-ppu-cgram.bin')).read_bytes(),capture['obsel'],rec['slots'])
        normalized={(x+48-g['draw_x'],y+68-g['draw_y']):color for (x,y),color in original.items()}
        if any(not (0<=x<96 and 0<=y<96) for x,y in normalized):raise ValueError('Pixel outside browser cell')
        for y in range(96):
            for x in range(96):
                offset=(y*96+x)*4;actual=frame[offset:offset+4];expected=normalized.get((x,y))
                if expected is None:
                    if actual[3]!=0:raise ValueError(f'Unexpected pixel frame {rec["tick"]} ({x},{y})')
                elif actual[3]!=255 or any(abs(actual[i]-expected[i])>1 for i in range(3)):
                    raise ValueError(f'Pixel mismatch frame {rec["tick"]} ({x},{y})')
    return len(records)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--asset',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();print('OK:',verify(a.root,a.asset,a.evidence),'browser frames match PPU pixels (RGB tolerance 1)')
