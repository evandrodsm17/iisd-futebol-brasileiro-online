"""Create a local replay demo from ROM descriptor rows and captured OAM."""
import argparse
import base64
import json
from pathlib import Path
from export_issd_team_motion import trace
from render_issd_descriptor_sprite import normalise_parts


def encode(data):return base64.b64encode(data).decode('ascii')


def export(root,graphics,output,trace_path,actor_geometry_root):
    report=json.loads((root/'descriptor-bridge.json').read_text(encoding='utf8'))
    graphics=json.loads(graphics.read_text(encoding='utf8'))
    if report['schema']!='issd-descriptor-oam-bridge/v1' or graphics['schema']!='issd-descriptor-graphics-local/v1' or report['rom_sha256']!=graphics['rom_sha256']:raise ValueError('Incompatible evidence')
    chosen={}
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    actor_rows=[json.loads(line) for line in (actor_geometry_root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    actor_geometry={row['step']:row for row in actor_rows if row.get('type')=='body_geometry'}
    origins={(row['step'],row['object']):row for row in rows if row.get('type')=='draw_entry'}
    anchors=json.loads((Path(__file__).resolve().parent.parent/'dist/data/issd-locomotion-anchors.json').read_text(encoding='utf8'))
    cycle=anchors['cycles']['walking'][4]
    by_descriptor={item['descriptor']:item for item in cycle['frames']}
    body_geometry=json.loads((Path(__file__).resolve().parent.parent/'dist/data/issd-locomotion-body-geometry.json').read_text(encoding='utf8'))
    if body_geometry.get('schema')!='issd-locomotion-body-geometry/v1' or body_geometry['rom_sha256']!=report['rom_sha256']:raise ValueError('Incompatible body geometry')
    observed={}
    for sample in trace(trace_path):
        for actor in sample.get('actors',[]):
            if actor['address']==0x0d00 and actor['direction']==4:observed.setdefault(actor['descriptor'],actor)
    hair_audit=json.loads((Path(__file__).resolve().parent.parent/'dist/data/issd-dynamic-hair-anchor-audit.json').read_text(encoding='utf8'))
    hair_by_descriptor={item['descriptor']:item for item in hair_audit['frames']}
    for row in report['frames']:chosen.setdefault(row['descriptor'],row)
    if len(chosen)!=10:raise ValueError('Expected ten verified locomotion descriptors')
    frames=[]
    for desc,row in sorted(chosen.items()):
        if not graphics['descriptors'][str(desc)].get('detail_validated'):raise ValueError(f'Detail tile not validated for {desc}')
        stem=root/f"frame-{row['ppu_step']:03d}"
        read=lambda suffix:Path(str(stem)+suffix).read_bytes()
        origin=origins[(row['step'],0x1700)];anchor=by_descriptor[desc]
        oam=read('-oam.bin');parts=normalise_parts(observed[desc]['parts']);slots=row['body_slots']
        if len(parts)!=len(slots):raise ValueError('Body part count mismatch')
        masks={p['attr']^oam[slot*4+3] for p,slot in zip(parts,slots)}
        if len(masks)!=1:raise ValueError('Inconsistent OAM attribute transformation')
        mask=masks.pop();hair_slot=row['hair_slot'];hair=hair_by_descriptor[desc]
        hair_x,hair_y,hair_tile,hair_attr=oam[hair_slot*4:hair_slot*4+4]
        hair_high=(oam[512+hair_slot//4]>>(2*(hair_slot%4)))&3
        if hair_high&1:hair_x-=512
        oy=(origin['draw_y']+origin['draw_z'])%65536
        if hair_high&2 or (hair_x-origin['draw_x'],hair_y-oy)!=(hair['hair_x'],hair['hair_y']):raise ValueError('Hair geometry mismatch')
        geometry=[{'slot':slot,'x':p['x'],'y':p['y'],'tile':p['tile'],'size':p['size'],'attr':p['attr']} for p,slot in zip(parts,slots)]
        actor_state=dict(actor_geometry[row['step']]);parts_from_rom=body_geometry['poses'][str(desc)]['parts']
        if actor_state['parts']!=parts_from_rom:raise ValueError('ROM body geometry differs from captured WRAM')
        actor_state['parts']=parts_from_rom
        frames.append({'descriptor':desc,'ppu_step':row['ppu_step'],'base_tile':row['base_tile'],'bank':row['bank'],'obsel':row['obsel'],
                       'actor_geometry':actor_state,
                       'origin_x':origin['draw_x'],'origin_y':oy,'attr_xor':mask,'geometry':geometry,
                       'hair_geometry':{'slot':hair_slot,'x':hair['hair_x'],'y':hair['hair_y'],'tile':hair_tile,'size':8,'attr':hair_attr},
                       'crop_x':origin['draw_x']-anchor['origin_x'],'crop_y':origin['draw_y']+origin['draw_z']-anchor['origin_y'],
                       'cell_width':cycle['cell_width'],'cell_height':cycle['cell_height'],
                       'slots':row['body_slots']+[row['hair_slot']],'hair_slot':row['hair_slot'],
                       'oam':encode(read('-oam.bin')),'vram':encode(read('-vram.bin')),'cgram':encode(read('-cgram.bin')),
                       'rows':graphics['descriptors'][str(desc)]['tiles_base64'],'detail_validated':True})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'schema':'issd-descriptor-bridge-demo-local/v1','frames':frames},separators=(',',':')),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('graphics',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--trace',type=Path,default=Path('docs/issd-match-trace-coverage.jsonl'))
    p.add_argument('--actor-geometry',type=Path,default=Path('analysis/bsnes-actor-oam-props'))
    a=p.parse_args();export(a.capture,a.graphics,a.output,a.trace,a.actor_geometry);print('Exported ten local descriptor/OAM frames')
