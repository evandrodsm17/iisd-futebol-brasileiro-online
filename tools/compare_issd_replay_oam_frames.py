"""Pair draw callbacks, prepared buffers and next-frame PPU pixel comparisons."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image
from analyze_issd_draw_trace import summarize
from analyze_issd_graphics_replay import compare_oam
from compare_issd_oam_pixels import compare, compose
from validate_issd_native_action_oam import validate


def audit(draw_rows, graphics_rows, graphics_root, actor):
    draw = summarize(draw_rows, actor)
    by_step = {r['step']: r for r in graphics_rows}
    by_frame = {r['frame']: r for r in graphics_rows}
    if len(by_step) != len(graphics_rows) or len(by_frame) != len(graphics_rows):
        raise ValueError('Duplicate graphics step or frame')
    results, skipped = [], []
    for entry in draw['entries']:
        prepared = by_step.get(entry['step'])
        if entry['status'] != 'observed-stack-range' or not prepared:
            skipped.append({'step': entry['step'], 'reason': 'missing slots or prepared frame'})
            continue
        if prepared['frame'] != entry['frame'] + 1:
            raise ValueError('Unexpected draw-callback to capture-frame relationship')
        ppu = by_frame.get(prepared['frame'] + 1)
        if not ppu or not ppu.get('oam_ppu') or not ppu.get('cgram_ppu') or not ppu.get('screenshot'):
            skipped.append({'step': entry['step'], 'reason': 'missing following PPU frame'})
            continue
        mirror = (graphics_root / prepared['oam_mirror']).read_bytes()
        oam = (graphics_root / ppu['oam_ppu']).read_bytes()
        if compare_oam(mirror, oam) != 0:
            skipped.append({'step': entry['step'], 'reason': 'prepared OAM does not match PPU'})
            continue
        pixels = compose(oam, (graphics_root / ppu['vram']).read_bytes(),
                         (graphics_root / ppu['cgram_ppu']).read_bytes(), ppu['obsel'],
                         entry['candidate_slots'])
        with Image.open(graphics_root / ppu['screenshot']) as image: metrics = compare(pixels, image)
        results.append({'step': entry['step'], 'prepared_frame': prepared['frame'],
                        'ppu_frame': ppu['frame'], 'script': prepared['actor']['animation_script'],
                        'descriptor': prepared['actor']['descriptor'],
                        'direction': prepared['actor']['direction'], 'slots': entry['candidate_slots'],
                        **metrics})
    return {'actor': actor, 'frames': results, 'skipped': skipped,
            'exact_nonempty_frames': sum(r['candidate_pixels'] > 0 and r['nonmatching_pixels'] == 0 for r in results),
            'limitations': ['Matching candidate pixels does not prove no actor pixels are missing.',
                            'PPU priority, blending and unobserved occluded pieces are not fully modeled.',
                            'Applies only to captured frames and the observed OAM stack path.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('draw_trace',type=Path);p.add_argument('graphics_trace',type=Path)
    p.add_argument('--actor',type=lambda s:int(s,0),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    validation=validate(a.graphics_trace)
    if not validation['valid']: raise ValueError('Graphics capture validation failed')
    def read(path):
        raw=path.read_bytes()
        return [json.loads(line) for line in raw.splitlines() if line.strip()], hashlib.sha256(raw).hexdigest()
    draw,dh=read(a.draw_trace);graphics,gh=read(a.graphics_trace)
    result=audit(draw,graphics,a.graphics_trace.parent,a.actor)
    result.update({'schema':'issd-replay-oam-frame-audit/v1',
                   'sources':[{'path':a.draw_trace.as_posix(),'sha256':dh},
                              {'path':a.graphics_trace.as_posix(),'sha256':gh}]})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('frames:',len(result['frames']),'exact:',result['exact_nonempty_frames'],'skipped:',len(result['skipped']))


if __name__=='__main__':main()
