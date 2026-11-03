"""Make local keeper pose hashes using the independent Python compositor."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image
from render_issd_descriptor_sprite import compose


def export(data,preview):
    cases=[]
    for team in (0,2,30):
        for skin in (0,1):
            palette=preview['teams'][team]['palettes'][2+skin]
            colors=[(round((word&31)*255/31),round(((word>>5)&31)*255/31),round(((word>>10)&31)*255/31),0 if i==0 else 255) for i,word in enumerate(palette)]
            for direction,cycle in enumerate(data['cycles']):
                for index,frame in enumerate(cycle['frames']):
                    if frame is None:continue
                    props=frame['props'];parts=[]
                    for p in frame['parts']:
                        signed=lambda n:n if n<32768 else n-65536
                        dx=signed(p['dx']);dy=signed(p['dy']);large=p['large']
                        if props&64:dx=-dx
                        attr=(p['attr']&0xc1)^props
                        if p['attr']&32:attr=attr|2 if attr&8 else (attr&0xfb)|8
                        parts.append({'x':dx-(8 if large else 4),'y':dy-(8 if large else 4),'tile':p['tile'],'size':16 if large else 8,'attr':attr})
                    left=min(p['x'] for p in parts);top=min(p['y'] for p in parts)
                    rendered=compose(base64.b64decode(frame['tiles']),parts,{i:colors for i in range(8)})
                    result=Image.new('RGBA',(cycle['width'],cycle['height']));result.alpha_composite(rendered,(left+frame['origin_x'],top+frame['origin_y']))
                    cases.append({'team':team,'skin':skin,'direction':direction,'frame':index,'sha256':hashlib.sha256(result.tobytes()).hexdigest()})
    return {'schema':'issd-goalkeeper-locomotion-hashes-local/v1','cases':cases}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('preview',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=export(json.loads(a.data.read_text(encoding='utf8')),json.loads(a.preview.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8');print(f"Generated {len(result['cases'])} keeper references")
