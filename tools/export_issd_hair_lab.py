"""Generate a local, layered diagnostic demo from exact emulator pixels."""
import argparse
import json
from pathlib import Path
from PIL import Image
from analyze_issd_hair_oam import analyze
from compare_issd_oam_pixels import compose,compare

SIZE=64


def export(cases,output):
    output.mkdir(parents=True,exist_ok=True)
    styles=[]
    for style,root in cases:
        report=analyze(root)
        trace=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
        graphics={r['frame']:r for r in trace if r.get('type')=='graphics'}
        selected=[f for f in report['frames'] if f['candidate_pixels'] and f['nonmatching_pixels']==0]
        if not selected:raise ValueError(f'No exact frames for style {style}')
        sheets={key:Image.new('RGBA',(SIZE*len(selected),SIZE)) for key in ('body','hair')}
        for n,frame in enumerate(selected):
            row=graphics[frame['ppu_frame']];stem=root/f"frame-{row['step']:03d}"
            read=lambda suffix:Path(str(stem)+suffix).read_bytes()
            oam,vram,cgram=read('-oam.bin'),read('-vram.bin'),read('-cgram.bin')
            hair_slots=[frame['hair_slot']];body_slots=frame['body_slots']
            if frame['hair_slot']>=min(body_slots):raise ValueError('Unexpected layer priority')
            body=compose(oam,vram,cgram,row['obsel'],body_slots)
            hair=compose(oam,vram,cgram,row['obsel'],hair_slots)
            combined=compose(oam,vram,cgram,row['obsel'],hair_slots+body_slots)
            with Image.open(str(stem)+'.png') as image:
                if compare(combined,image)['nonmatching_pixels']:raise ValueError('Reference frame no longer matches')
            points=set(body)|set(hair)
            if not points:raise ValueError('Empty captured frame')
            left=min(x for x,y in points);top=min(y for x,y in points)
            width=max(x for x,y in points)-left+1;height=max(y for x,y in points)-top+1
            if width>SIZE or height>SIZE:raise ValueError('Captured frame exceeds diagnostic cell')
            dx=n*SIZE+(SIZE-width)//2-left;dy=SIZE-height-2-top
            for layer,pixels in (('body',body),('hair',hair)):
                for (x,y),rgb in pixels.items():sheets[layer].putpixel((x+dx,y+dy),(*rgb,255))
        for layer,image in sheets.items():image.save(output/f'style-{style}-{layer}.png')
        styles.append({'style':style,'frames':len(selected),'steps':[f['step'] for f in selected],
                       'body':f'style-{style}-body.png','hair':f'style-{style}-hair.png'})
    manifest={'schema':'issd-hair-lab-local/v1','cell_size':SIZE,'styles':styles,
              'limitations':['Diagnostic replay; actor positioning and styles 2/13 are synthetic.',
                             'Only exact visible frames of one direction and captured palette are included.',
                             'This is not yet the game runtime renderer.']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--style1',required=True,type=Path)
    p.add_argument('--style2',required=True,type=Path);p.add_argument('--style13',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=export([(1,a.style1),(2,a.style2),(13,a.style13)],a.output)
    print('Prévia local criada:',', '.join(f"estilo {s['style']}: {s['frames']} quadros" for s in result['styles']))
