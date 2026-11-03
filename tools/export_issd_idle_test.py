"""Build local pose reference hashes from captured VRAM/CGRAM renderer."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image
from render_issd_action_vram_capture import render


def export(data,trace_path):
    rows=[json.loads(line) for line in trace_path.read_text(encoding='utf8').splitlines() if line.strip()]
    index={(r['actor']['animation_script'],r['actor']['direction'],r['actor']['descriptor']):r for r in rows}
    output=[]
    for name,script in (('idle',0xd320),('idle_with_ball',0xd6db)):
        for cycle in data['cycles'][name]:
            for frame in cycle['frames']:
                row=index[(script,cycle['direction'],frame['descriptor'])];parts=row['actor']['parts']
                left=min(p['x'] for p in parts);top=min(p['y'] for p in parts)
                image=Image.new('RGBA',(cycle['width'],cycle['height']));image.alpha_composite(render(row),(left-cycle['left'],top-cycle['top']))
                output.append({'name':name,'direction':cycle['direction'],'descriptor':frame['descriptor'],
                               'sha256':hashlib.sha256(image.tobytes()).hexdigest()})
    return {'schema':'issd-idle-reference-hashes-local/v1','frames':output}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=export(json.loads(a.data.read_text(encoding='utf8')),a.trace);a.output.write_text(json.dumps(r,separators=(',',':')),encoding='utf8')
    print(f"Prepared {len(r['frames'])} observed idle references")
