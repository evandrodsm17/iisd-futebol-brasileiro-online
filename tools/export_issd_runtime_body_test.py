"""Build ignored local hashes of existing sheets for runtime equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def export(data,assets,catalog):
    results=[]
    for team in (0,2,30):
        for kit in ('home','away'):
            palette=catalog['teams'][team]['kit'][kit]['sprite_palette']
            for motion,cycles in data['cycles'].items():
                for direction,cycle in enumerate(cycles):
                    with Image.open(assets/f'{team:02d}'/kit/f'{motion}-{direction}.png') as im:
                        sheet=im.convert('RGBA')
                        if sheet.size!=(cycle['width']*len(cycle['frames']),cycle['height']):raise ValueError('Sheet dimensions mismatch')
                        for index in range(len(cycle['frames'])):
                            pixels=sheet.crop((index*cycle['width'],0,(index+1)*cycle['width'],cycle['height'])).tobytes()
                            results.append({'team':team,'kit':kit,'motion':motion,'direction':direction,'frame':index,
                                            'palette':palette,'sha256':hashlib.sha256(pixels).hexdigest()})
    return {'schema':'issd-runtime-body-sheet-hashes-local/v1','frames':results}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('data',type=Path);p.add_argument('assets',type=Path);p.add_argument('catalog',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=export(json.loads(a.data.read_text(encoding='utf8')),a.assets,json.loads(a.catalog.read_text(encoding='utf8')))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8');print(f"Generated {len(result['frames'])} local reference hashes")
