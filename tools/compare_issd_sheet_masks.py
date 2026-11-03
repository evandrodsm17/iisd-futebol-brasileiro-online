"""Compare sprite-sheet silhouettes up to integer translation, ignoring colours."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image


def mask(image):
    rgba=image.convert('RGBA')
    return {(x,y) for y in range(rgba.height) for x in range(rgba.width)
            if rgba.getpixel((x,y))[3] != 0}


def compare_masks(reference, candidate):
    if not reference or not candidate: raise ValueError('A frame has no opaque pixels')
    shifts=Counter((bx-ax,by-ay) for ax,ay in reference for bx,by in candidate)
    # Stable tie-breaking; translation is a measurement, not a new sprite anchor.
    (dx,dy),overlap=min(shifts.items(),key=lambda item:(-item[1],abs(item[0][0])+abs(item[0][1]),item[0]))
    return {'reference_pixels':len(reference),'candidate_pixels':len(candidate),
            'best_translation':[dx,dy],'overlap':overlap,
            'reference_only':len(reference)-overlap,'candidate_only':len(candidate)-overlap,
            'identical_up_to_translation':overlap==len(reference)==len(candidate)}


def compare_sheets(reference,candidate,reference_cell,candidate_cell,frames):
    rw,rh=reference_cell; cw,ch=candidate_cell
    if min(rw,rh,cw,ch,frames)<=0 or reference.size!=(rw*frames,rh) or candidate.size!=(cw*frames,ch):
        raise ValueError('Image dimensions must exactly match the declared cells and frame count')
    return [compare_masks(mask(reference.crop((i*rw,0,(i+1)*rw,rh))),
                          mask(candidate.crop((i*cw,0,(i+1)*cw,ch)))) for i in range(frames)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--reference-cell',nargs=2,type=int,required=True)
    p.add_argument('--candidate-cell',nargs=2,type=int,required=True)
    p.add_argument('--frames',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    with Image.open(a.reference) as ref, Image.open(a.candidate) as cand:
        frames=compare_sheets(ref,cand,a.reference_cell,a.candidate_cell,a.frames)
    result={'schema':'issd-sheet-mask-comparison/v1','frames':frames,
            'sources':[{'path':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                       for path in (a.reference,a.candidate)],
            'limitations':['Compares only alpha silhouettes, not palette colours or animation timing.',
                           'Alignment is chosen independently per frame and is not a validated anchor.',
                           'Reference captures can omit occluded actor parts or include unrelated objects.',
                           'A difference does not identify its cause or prove either source is complete.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('matching masks:',sum(x['identical_up_to_translation'] for x in frames),'/',len(frames))


if __name__=='__main__':main()
