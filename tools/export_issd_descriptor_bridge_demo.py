"""Create a local replay demo from ROM descriptor rows and captured OAM."""
import argparse
import base64
import json
from pathlib import Path


def encode(data):return base64.b64encode(data).decode('ascii')


def export(root,graphics,output):
    report=json.loads((root/'descriptor-bridge.json').read_text(encoding='utf8'))
    graphics=json.loads(graphics.read_text(encoding='utf8'))
    if report['schema']!='issd-descriptor-oam-bridge/v1' or graphics['schema']!='issd-descriptor-graphics-local/v1' or report['rom_sha256']!=graphics['rom_sha256']:raise ValueError('Incompatible evidence')
    chosen={}
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    origins={(row['step'],row['object']):row for row in rows if row.get('type')=='draw_entry'}
    anchors=json.loads((Path(__file__).resolve().parent.parent/'dist/data/issd-locomotion-anchors.json').read_text(encoding='utf8'))
    cycle=anchors['cycles']['walking'][4]
    by_descriptor={item['descriptor']:item for item in cycle['frames']}
    for row in report['frames']:chosen.setdefault(row['descriptor'],row)
    if len(chosen)!=10:raise ValueError('Expected ten verified locomotion descriptors')
    frames=[]
    for desc,row in sorted(chosen.items()):
        stem=root/f"frame-{row['ppu_step']:03d}"
        read=lambda suffix:Path(str(stem)+suffix).read_bytes()
        origin=origins[(row['step'],0x1700)];anchor=by_descriptor[desc]
        frames.append({'descriptor':desc,'base_tile':row['base_tile'],'bank':row['bank'],'obsel':row['obsel'],
                       'crop_x':origin['draw_x']-anchor['origin_x'],'crop_y':origin['draw_y']+origin['draw_z']-anchor['origin_y'],
                       'cell_width':cycle['cell_width'],'cell_height':cycle['cell_height'],
                       'slots':row['body_slots']+[row['hair_slot']],
                       'oam':encode(read('-oam.bin')),'vram':encode(read('-vram.bin')),'cgram':encode(read('-cgram.bin')),
                       'rows':graphics['descriptors'][str(desc)]['tiles_base64']})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':'issd-descriptor-bridge-demo-local/v1','frames':frames},separators=(',',':')),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('graphics',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.capture,a.graphics,a.output);print('Exported ten local descriptor/OAM frames')
