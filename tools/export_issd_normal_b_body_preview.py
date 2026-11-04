"""Export locally verified normal-B body poses; no ROM or image is distributed."""
import argparse,json
from pathlib import Path
from PIL import Image
from audit_issd_normal_b_body import audit
from compare_issd_oam_pixels import compose


def export(root,control,rom,state,output):
    report=audit(root,control,rom,state)
    drawings=[json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()]
    captures={r['frame']:r for x in (root/'slide-poses.jsonl').read_text().splitlines() if (r:=json.loads(x))}
    sheet=Image.new('RGBA',(192,96))
    for index,frame in enumerate(report['frames']):
        geometry=next(r for r in drawings if r.get('type')=='body_geometry' and r['frame']==frame['draw_frame'] and r['object']==report['actor'])
        capture=captures[frame['displayed_frame']];stem=capture['stem']
        pixels=compose((root/(stem+'-ppu.bin')).read_bytes(),(root/(stem+'-vram.bin')).read_bytes(),
                       (root/(stem+'-ppu-cgram.bin')).read_bytes(),capture['obsel'],frame['slots'])
        for (x,y),rgb in pixels.items():
            px=x-geometry['draw_x']+48+96*index;py=y-((geometry['draw_y']+geometry['draw_z'])&65535)+68
            if not 96*index<=px<96*(index+1) or not 0<=py<96:raise ValueError('Body exceeds preview cell')
            sheet.putpixel((px,py),(*rgb,255))
    output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output)
    return len(report['frames'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--control',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print('exported local verified body frames:',export(a.root,a.control,a.rom,a.state,a.output))
