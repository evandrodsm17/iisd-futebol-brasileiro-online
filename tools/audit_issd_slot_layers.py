"""Inspect palette banks and pixel overlaps within selected OAM slots."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from compare_issd_oam_pixels import compare,compose


def audit(oam,vram,cgram,obsel,slots,image):
    # Also validates slot values and capture dimensions.
    compose(oam,vram,cgram,obsel,slots)
    parts=[]; masks={}
    for slot in slots:
        pixels=compose(oam,vram,cgram,obsel,[slot]);masks[slot]=set(pixels)
        parts.append({'slot':slot,'palette_bank':(oam[slot*4+3]>>1)&7,**compare(pixels,image)})
    overlaps=[{'earlier_slot':a,'later_slot':b,'overlap_pixels':len(masks[a]&masks[b])}
              for a in slots for b in slots if a<b and masks[a]&masks[b]]
    return {'slots':parts,'overlaps':overlaps,
            'limitations':['Slot colors and overlapping pixels do not establish the semantic identity of a part.',
                           'Other sprites, PPU priority and background can alter the final screenshot.',
                           'The supplied slot-to-actor association must be validated independently.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('graphics_trace',type=Path)
    p.add_argument('--frame',type=int,required=True);p.add_argument('--slots',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.graphics_trace.read_bytes()
    rows=[r for r in (json.loads(l) for l in raw.splitlines() if l.strip()) if r['frame']==a.frame]
    if len(rows)!=1:raise ValueError('Missing or ambiguous frame')
    r=rows[0];root=a.graphics_trace.parent
    with Image.open(root/r['screenshot']) as im:
        result=audit((root/r['oam_ppu']).read_bytes(),(root/r['vram']).read_bytes(),
                     (root/r['cgram_ppu']).read_bytes(),r['obsel'],[int(x) for x in a.slots.split(',')],im)
    result.update({'schema':'issd-slot-layer-audit/v1','frame':a.frame,
                   'source':{'path':a.graphics_trace.as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('slots:',len(result['slots']),'overlaps:',len(result['overlaps']))


if __name__=='__main__':main()
