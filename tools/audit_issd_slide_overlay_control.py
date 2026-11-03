"""Compare slide pixel mismatches with the same-frame neutral replay."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from audit_issd_slide_oam_replay import audit as audit_oam
from compare_issd_oam_pixels import compose
from compare_issd_action_trials import load


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(action_root,control_root,asset_map,state):
    traces=list(control_root.glob('issd-auto-probe-*.jsonl'))
    if len(traces)!=1: raise ValueError('Expected one neutral replay trace')
    result=audit_oam(action_root,traces[0],asset_map,state)
    trace=load(traces[0]); samples=trace['samples']
    poses={r['frame']:r for r in (json.loads(line) for line in (action_root/'slide-poses.jsonl').read_text().splitlines() if line.strip())}
    captures=[json.loads(line) for line in (control_root/'overlay-control.jsonl').read_text().splitlines() if line.strip()]
    by_frame={r['frame']:r for r in captures}
    if len(by_frame)!=6 or len(captures)!=6 or not all(r['success'] for r in captures):
        raise ValueError('Expected six unique control screenshots')
    rows=[]
    for frame in result['frames']:
        n=frame['frame']; capture=by_frame.get(n)
        if not capture or not any(r['frame']==n and r['held_p1']==0 for r in samples.values()):
            raise ValueError(f'Missing neutral control frame {n}')
        stem=f"slide-{frame['script']:04X}-{frame['descriptor']:04X}"
        o=(action_root/(stem+'-ppu.bin')).read_bytes()
        v=(action_root/(stem+'-vram.bin')).read_bytes()
        c=(action_root/(stem+'-ppu-cgram.bin')).read_bytes()
        pixels=compose(o,v,c,poses[n]['obsel'],frame['candidate_slots'])
        screenshot=action_root/(stem+'-screen.png'); control=control_root/capture['screenshot']
        with Image.open(screenshot) as image,Image.open(control) as reference:
            if image.size!=(256,224) or reference.size!=(256,224): raise ValueError('Unexpected screenshot size')
            image=image.convert('RGB');reference=reference.convert('RGB')
            mismatches=[{'x':x,'y':y,'candidate':list(rgb),'action':list(image.getpixel((x,y))),
                         'control':list(reference.getpixel((x,y)))}
                        for (x,y),rgb in pixels.items() if image.getpixel((x,y))!=rgb]
        if len(mismatches)!=frame['unexplained_mismatches']:
            raise ValueError('Mismatch count changed')
        rows.append({'frame':n,'descriptor':frame['descriptor'],'candidate_slots':frame['candidate_slots'],
                     'mismatches':mismatches,'same_in_control':sum(p['action']==p['control'] for p in mismatches),
                     'control_screenshot_sha256':digest(control)})
    return {'schema':'issd-slide-overlay-control/v1','baseline_samples':result['baseline_samples'],
            'draw_trace_sha256':result['draw_trace_sha256'],'control_trace_sha256':trace['sha256'],
            'control_capture_sha256':digest(control_root/'overlay-control.jsonl'),'frames':rows,
            'limitations':['Same RGB pixel in both screenshots is evidence of a shared overlay, not proof of its PPU layer.',
                           'Candidate slots do not establish complete actor coverage or exact animation phase.',
                           'Control and action differ after the command; only recorded fields before it were compared.',
                           'One replay, one actor and one direction; no general spritesheet validation.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--asset-map',required=True,type=Path);p.add_argument('--state',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=audit(a.action,a.control,a.asset_map,a.state)
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('mismatches:',sum(len(f['mismatches']) for f in r['frames']), 'matching control:',sum(f['same_in_control'] for f in r['frames']))
