"""Export locally captured and pixel-validated penalty-ball frames for the lab."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from compare_issd_oam_pixels import compose, compare


def export(small_path, large_path, analysis_root, output_dir):
    small = json.loads(small_path.read_bytes())
    large = json.loads(large_path.read_bytes())
    if small['schema'] != 'issd-penalty-directional-projection/v1' or large['schema'] != 'issd-penalty-large-ball-projection/v1':
        raise ValueError('Unexpected projection reports')
    sheet = Image.new('RGBA', (1280,16))
    captures = []
    for capture_index, (small_capture, large_capture) in enumerate(zip(small['captures'],large['captures'])):
        if small_capture['name'] != large_capture['name'] or small_capture['input_direction'] != large_capture['input_direction']:
            raise ValueError('Projection captures do not match')
        root = analysis_root/small_capture['name']
        manifest = (root/'graphics.jsonl').read_bytes()
        if hashlib.sha256(manifest).hexdigest() != small_capture['graphics_sha256'] or hashlib.sha256(manifest).hexdigest() != large_capture['graphics_sha256']:
            raise ValueError('Capture manifest changed')
        rows = [json.loads(line) for line in manifest.splitlines()]
        samples = {e['frame']:e for e in rows if e.get('type')=='full_graphics'}
        if sorted(e['delta'] for e in samples.values()) != list(range(1,41)):
            raise ValueError('Incomplete capture')
        frames = [None]*40
        for report,size,count in ((small_capture,8,32),(large_capture,16,68)):
            for observed in report['samples']:
                sample = samples[observed['frame']]
                frame_index = sample['delta']-1
                if frames[frame_index] is not None:
                    raise ValueError('Overlapping validated frames')
                candidates = [entry for entry in observed['candidates'] if entry['lag']==2]
                if len(candidates)!=1 or not candidates[0]['matches_both']:
                    raise ValueError('No validated projection candidate')
                entry = candidates[0]
                stem = sample['stem']; slot = entry.get('slot')
                if slot is None:
                    # The small-part report omits the slot. Resolve it from the draw stack.
                    from analyze_issd_draw_trace import slots
                    draw = [e for e in rows if e.get('type')=='draw_entry' and e['frame']==entry['draw_frame']]
                    indexes = [i for i,e in enumerate(draw) if e['object']==0x700]
                    if len(indexes)!=1 or indexes[0]+1>=len(draw): raise ValueError('Missing draw entry')
                    index=indexes[0]; selected=slots(draw[index]['stack'],draw[index+1]['stack'])
                    if len(selected)!=1: raise ValueError('Unexpected OAM slot count')
                    slot=selected[0]
                oam,vram,cgram=[(root/f'{stem}-{kind}.bin').read_bytes() for kind in ('oam','vram','cgram')]
                pixels=compose(oam,vram,cgram,sample['obsel'],[slot])
                screenshot=root/f'{stem}.png'
                if hashlib.sha256(screenshot.read_bytes()).hexdigest()!=observed['screenshot_sha256']:
                    raise ValueError('Screenshot changed')
                with Image.open(screenshot) as image:
                    check=compare(pixels,image)
                if check['candidate_pixels']!=count or check['exact_rgb_matches']!=count:
                    raise ValueError('Ball pixels no longer match')
                x,y=oam[4*slot],oam[4*slot+1]
                if [x,y]!=[entry['oam_x'],entry['oam_y']]: raise ValueError('OAM position changed')
                for (px,py),color in pixels.items():
                    if not (0<=px-x<size and 0<=py-y<size): raise ValueError('Pixels outside expected sprite')
                    sheet.putpixel(((capture_index*40+frame_index)*16+px-x,py-y),(*color,255))
                frames[frame_index]={'x':x,'y':y,'size':size,'slot':slot}
        if sum(frame is not None for frame in frames)!=34: raise ValueError('Unexpected validated frame count')
        captures.append({'input':small_capture['input_direction'],'frames':frames})
    output_dir.mkdir(parents=True,exist_ok=True)
    image_path=output_dir/'penalty-ball-observed-local.png'
    json_path=output_dir/'penalty-ball-observed-local.json'
    sheet.save(image_path)
    json_path.write_text(json.dumps({'schema':'issd-penalty-ball-preview/v1','atlas':'penalty-ball-observed-local.png',
                                     'atlas_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                                     'frame_count':40,'captures':captures},indent=2)+'\n',encoding='utf8')
    return image_path,json_path


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('small','large','analysis','output'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    image,manifest=export(args.small,args.large,args.analysis,args.output)
    print(f'OK: 68 validated frames exported locally: {image.name}, {manifest.name}')
