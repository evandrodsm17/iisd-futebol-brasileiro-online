"""Classify mismatching candidate pixels covered by earlier OAM slots."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from compare_issd_oam_pixels import compose


def classify(candidate, earlier, screenshot):
    if screenshot.size != (256,224): raise ValueError('Expected native screenshot')
    image=screenshot.convert('RGB')
    mismatch={pos for pos,rgb in candidate.items() if image.getpixel(pos)!=rgb}
    covered={pos for pos in mismatch if pos in earlier and earlier[pos]==image.getpixel(pos)}
    return {'candidate_pixels':len(candidate),'direct_matches':len(candidate)-len(mismatch),
            'mismatches_explained_by_earlier_slots':len(covered),
            'unexplained_mismatches':len(mismatch-covered)}


def audit(frame_audit,graphics,root):
    by_frame={r['frame']:r for r in graphics}
    if len(by_frame)!=len(graphics):raise ValueError('Duplicate graphics frame')
    results=[]
    for frame in frame_audit['frames']:
        slots=frame['slots']
        if not slots:continue
        row=by_frame[frame['ppu_frame']]
        oam=(root/row['oam_ppu']).read_bytes(); vram=(root/row['vram']).read_bytes()
        cgram=(root/row['cgram_ppu']).read_bytes()
        candidate=compose(oam,vram,cgram,row['obsel'],slots)
        earlier=compose(oam,vram,cgram,row['obsel'],list(range(min(slots))))
        with Image.open(root/row['screenshot']) as image:values=classify(candidate,earlier,image)
        results.append({'ppu_frame':frame['ppu_frame'],'script':frame['script'],
                        'descriptor':frame['descriptor'],'direction':frame['direction'],
                        'slots':slots,**values})
    return {'frames':results,
            'limitations':['An RGB match to an earlier slot suggests but does not prove the cause of an overlap.',
                           'OAM priority, sprite-per-line limits, background and colour math are not fully simulated.',
                           'Unexplained mismatches must not be automatically discarded.',
                           'Candidate pixel matches do not establish complete actor coverage.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('frame_audit',type=Path);p.add_argument('graphics_trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    ar=a.frame_audit.read_bytes();gr=a.graphics_trace.read_bytes()
    result=audit(json.loads(ar),[json.loads(l) for l in gr.splitlines() if l.strip()],a.graphics_trace.parent)
    result.update({'schema':'issd-candidate-occlusion-audit/v1','sources':[
        {'path':a.frame_audit.as_posix(),'sha256':hashlib.sha256(ar).hexdigest()},
        {'path':a.graphics_trace.as_posix(),'sha256':hashlib.sha256(gr).hexdigest()}]})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('frames:',len(result['frames']),'unexplained:',sum(x['unexplained_mismatches'] for x in result['frames']))


if __name__=='__main__':main()
