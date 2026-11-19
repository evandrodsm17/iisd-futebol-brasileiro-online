"""Build local goalie layers synchronized with pixel-validated penalty-ball captures."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from PIL import Image
from compare_issd_oam_pixels import compose, compare
from export_issd_penalty_keeper_continuous import export as export_keeper


def export(analysis_root, output_dir):
    captures=[]
    output_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='issd-keeper-preview-') as temporary:
        scratch=Path(temporary)
        for direction in ('Left','Right'):
            root=analysis_root/f'penalty-projection-{direction}-v3'
            # Existing exporter independently verifies draw-list slots, screenshots and occlusion.
            report=export_keeper(root,scratch/f'{direction}.png',scratch/f'{direction}.json')
            raw=(root/'graphics.jsonl').read_bytes()
            if hashlib.sha256(raw).hexdigest()!=report['manifest_sha256']:
                raise ValueError('Capture changed during export')
            rows=[json.loads(line) for line in raw.splitlines()]
            samples={e['frame']:e for e in rows if e.get('type')=='full_graphics'}
            left,top,right,bottom=report['screen_bounds']
            width,height=right-left,bottom-top
            if width!=report['cell_width'] or height!=report['cell_height']:
                raise ValueError('Invalid keeper bounds')
            sheet=Image.new('RGBA',(width*40,height))
            available=[False]*40
            for frame in report['frames']:
                sample=samples[frame['capture_frame']]
                if sample['delta']!=frame['delta'] or available[frame['delta']-1]:
                    raise ValueError('Ambiguous keeper frame')
                stem=sample['stem']
                oam,vram,cgram=[(root/f'{stem}-{kind}.bin').read_bytes() for kind in ('oam','vram','cgram')]
                pixels=compose(oam,vram,cgram,sample['obsel'],frame['slots'])
                with Image.open(root/f'{stem}.png') as image:
                    check=compare(pixels,image)
                    if check['candidate_pixels']!=frame['pixels'] or check['exact_rgb_matches']!=frame['direct_matches']:
                        raise ValueError('Keeper pixels changed')
                    # Retain all captured keeper pixels; exact priority over other sprites is unresolved.
                    for (x,y),color in pixels.items():
                        if not (left<=x<right and top<=y<bottom):raise ValueError('Keeper outside atlas bounds')
                        sheet.putpixel(((frame['delta']-1)*width+x-left,y-top),(*color,255))
                available[frame['delta']-1]=True
            name=f'penalty-scene-keeper-{direction.lower()}-local.png'
            image_path=output_dir/name
            sheet.save(image_path)
            captures.append({'input':direction,'atlas':name,'atlas_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                             'graphics_sha256':report['manifest_sha256'],'width':width,'height':height,
                             'x':left,'y':top,'frames':available})
    manifest=output_dir/'penalty-scene-observed-local.json'
    manifest.write_text(json.dumps({'schema':'issd-penalty-scene-preview/v1','frame_count':40,'captures':captures},indent=2)+'\n',encoding='utf8')
    return captures


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('analysis',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=export(args.analysis,args.output)
    print('OK: synchronized keeper layers',[(item['input'],sum(item['frames'])) for item in result])
