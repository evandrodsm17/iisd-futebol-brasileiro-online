"""Build local-only RGBA reference fixtures from audited BizHawk captures."""
import argparse
import base64
import json
from pathlib import Path
from compare_issd_oam_pixels import compose


def export(root, output, demo_output=None):
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    graphics={r['frame']:r for r in rows if r.get('type')=='graphics'}
    audit=json.loads((root/'oam-audit.json').read_text(encoding='utf8'))
    output.mkdir(parents=True,exist_ok=True)
    fixtures=[]
    for item in audit['frames']:
        if item['nonmatching_pixels'] or not item['candidate_pixels']:continue
        graphic=graphics[item['ppu_frame']];step=graphic['step'];prefix=f'frame-{step:03d}'
        slots=item['body_slots']+[item['hair_slot']]
        oam=(root/f'{prefix}-oam.bin').read_bytes();vram=(root/f'{prefix}-vram.bin').read_bytes()
        cgram=(root/f'{prefix}-cgram.bin').read_bytes()
        pixels=compose(oam,vram,cgram,graphic['obsel'],slots)
        rgba=bytearray(256*224*4)
        for (x,y),rgb in pixels.items():rgba[(y*256+x)*4:(y*256+x)*4+4]=bytes((*rgb,255))
        expected=f'{prefix}-expected.rgba';(output/expected).write_bytes(rgba)
        fixtures.append({'step':step,'prefix':prefix,'slots':slots,'obsel':graphic['obsel'],'expected':expected,'pixels':len(pixels)})
        if demo_output and item['step']==20:
            demo={'schema':'issd-oam-demo-local/v1','obsel':graphic['obsel'],'slots':slots,
                  'oam':base64.b64encode(oam).decode('ascii'),'vram':base64.b64encode(vram).decode('ascii'),
                  'cgram':base64.b64encode(cgram).decode('ascii')}
            demo_output.parent.mkdir(parents=True,exist_ok=True)
            demo_output.write_text(json.dumps(demo,separators=(',',':')),encoding='utf8')
    if not fixtures:raise ValueError('No exact nonempty candidate frames')
    (output/'manifest.json').write_text(json.dumps({'schema':'issd-oam-fixtures-local/v1','capture':str(root.resolve()),'frames':fixtures},indent=2)+'\n',encoding='utf8')
    return len(fixtures)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('capture',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--demo-output',type=Path,help='Optional ignored browser preview data')
    args=parser.parse_args();print(f'Generated {export(args.capture,args.output,args.demo_output)} local fixtures')
