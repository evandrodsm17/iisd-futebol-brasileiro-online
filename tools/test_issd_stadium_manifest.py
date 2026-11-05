"""Check that the stadium manifest matches the actual configured PNG bounds."""
import json
from pathlib import Path
from PIL import Image,ImageChops

manifest=json.loads(Path('dist/data/issd-stadium-layouts.json').read_text(encoding='utf8'))
assert len(manifest['layouts'])==8
for entry in manifest['layouts']:
    path=Path('dist')/entry['asset'].removeprefix('./')
    image=Image.open(path).convert('RGB')
    bounds=ImageChops.difference(image,Image.new('RGB',image.size)).getbbox()
    assert bounds is not None,entry['id']
    left,top,right,bottom=bounds
    assert entry['image']=={'width':image.width,'height':image.height},entry['id']
    assert entry['crop']=={'x':left,'y':top,'w':right-left,'h':bottom-top},entry['id']
print('OK: dimensões e recortes dos oito estádios correspondem aos arquivos')
