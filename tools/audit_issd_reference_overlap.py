"""Compare unmatched candidate pixels with a second replay's screenshot."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from compare_issd_oam_pixels import compose


def classify(candidate, screenshot, reference):
    if screenshot.size != (256,224) or reference.size != (256,224):
        raise ValueError('Screenshots must both be native 256x224')
    image=screenshot.convert('RGB'); baseline=reference.convert('RGB')
    unmatched=[pos for pos,rgb in candidate.items() if image.getpixel(pos)!=rgb]
    same=[pos for pos in unmatched if image.getpixel(pos)==baseline.getpixel(pos)]
    return {'candidate_pixels':len(candidate),'unmatched_pixels':len(unmatched),
            'unmatched_matching_reference':len(same),'remaining_unmatched':len(unmatched)-len(same)}


def audit(frame_audit, graphics, reference, root, reference_root):
    by_frame={r['frame']:r for r in graphics}; base={r['frame']:r for r in reference}
    if len(by_frame)!=len(graphics) or len(base)!=len(reference):raise ValueError('Duplicate frame')
    results=[]
    for frame in frame_audit['frames']:
        f=frame['ppu_frame']
        if f not in base: continue
        a,b=by_frame[f],base[f]
        pixels=compose((root/a['oam_ppu']).read_bytes(),(root/a['vram']).read_bytes(),
                       (root/a['cgram_ppu']).read_bytes(),a['obsel'],frame['slots'])
        with Image.open(root/a['screenshot']) as image, Image.open(reference_root/b['screenshot']) as baseline:
            metrics=classify(pixels,image,baseline)
        results.append({'ppu_frame':f,'script':frame['script'],'descriptor':frame['descriptor'],**metrics})
    return {'frames':results,'limitations':['Same-colour pixels across screenshots suggest a shared layer but do not identify it.',
            'Replays diverged in their inputs and actor positions; only same-coordinate RGB was compared.',
            'This does not resolve PPU priority, colour math or unobserved actor parts.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('frame_audit',type=Path);p.add_argument('graphics',type=Path);p.add_argument('reference',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    data=[path.read_bytes() for path in (a.frame_audit,a.graphics,a.reference)]
    result=audit(json.loads(data[0]),[json.loads(x) for x in data[1].splitlines() if x.strip()],
                 [json.loads(x) for x in data[2].splitlines() if x.strip()],a.graphics.parent,a.reference.parent)
    result.update({'schema':'issd-reference-overlap/v1','sources':[{'path':path.as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
                  for path,raw in zip((a.frame_audit,a.graphics,a.reference),data)]})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('frames:',len(result['frames']))


if __name__=='__main__':main()
