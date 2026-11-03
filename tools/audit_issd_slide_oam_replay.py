"""Compare passive draw-list candidate slots against replay screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from analyze_issd_draw_trace import slots
from audit_issd_candidate_occlusion import classify
from audit_issd_slide_visual_replay import audit as audit_visual
from compare_issd_oam_pixels import compose


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, neutral, asset_map, state):
    visual=audit_visual(root,neutral,asset_map,state)
    draw_path=root/'slide-draw.jsonl'
    draw=[r for r in (json.loads(line) for line in draw_path.read_text().splitlines() if line.strip()) if not r.get('type')]
    snapshots=[json.loads(line) for line in (root/'slide-poses.jsonl').read_text().splitlines() if line.strip()]
    frames=[]
    for snapshot in snapshots:
        # The draw callback occurs during frameadvance, before frame-end.
        draw_frame=snapshot['frame']-1
        events=[e for e in draw if e['frame']==draw_frame]
        matches=[i for i,e in enumerate(events) if e['object']==snapshot['actor']]
        if len(matches)!=1 or matches[0]+1>=len(events):
            raise ValueError(f'Missing unique actor draw range at frame {draw_frame}')
        i=matches[0]
        candidate=slots(events[i]['stack'],events[i+1]['stack'])
        if not candidate: raise ValueError('Empty draw range')
        stem=snapshot['stem']
        ppu=root/(stem+'-ppu.bin');vram=root/(stem+'-vram.bin')
        cgram=root/(stem+'-ppu-cgram.bin');shot=root/(stem+'-screen.png')
        if not snapshot.get('ppu_available') or not snapshot.get('ppu_cgram_available') or not snapshot.get('screenshot'):
            raise ValueError('PPU graphics or screenshot unavailable')
        o,v,c=ppu.read_bytes(),vram.read_bytes(),cgram.read_bytes()
        candidate_pixels=compose(o,v,c,snapshot['obsel'],candidate)
        earlier_pixels=compose(o,v,c,snapshot['obsel'],list(range(min(candidate))))
        with Image.open(shot) as image: comparison=classify(candidate_pixels,earlier_pixels,image)
        frames.append({'frame':snapshot['frame'],'draw_frame':draw_frame,'actor':snapshot['actor'],
                       'script':snapshot['script'],'descriptor':snapshot['descriptor'],
                       'candidate_slots':candidate,'stack_before':events[i]['stack'],
                       'stack_after':events[i+1]['stack'],**comparison,
                       'local_files_sha256':{name:digest(path) for name,path in
                         [('ppu',ppu),('vram',vram),('ppu_cgram',cgram),('screenshot',shot)]}})
    if len(frames)!=6: raise ValueError('Expected six observed poses')
    return {'schema':'issd-slide-oam-replay/v1','draw_trace_sha256':digest(draw_path),
            'visual_trace_sha256':visual['trace_sha256'],'neutral_trace_sha256':visual['neutral_trace_sha256'],
            'baseline_samples':visual['baseline_samples'],'frames':frames,
            'limitations':['Stack ranges are candidate slot assignments, not proof of complete actor coverage.',
                           'Frame offset follows this callback ordering; independent phase validation is still required.',
                           'Other objects, backgrounds, SNES priority and color math can affect pixel comparisons.',
                           'Unexplained mismatches remain unvalidated and may not be silently discarded.',
                           'One actor and one internal direction; no validated animation export.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('--neutral',type=Path,required=True)
    p.add_argument('--asset-map',type=Path,required=True);p.add_argument('--state',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit(a.root,a.neutral,a.asset_map,a.state)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('poses:',len(result['frames']),'unexplained:',sum(f['unexplained_mismatches'] for f in result['frames']))
