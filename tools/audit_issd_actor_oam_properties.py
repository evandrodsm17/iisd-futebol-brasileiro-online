"""Check actor WRAM geometry/property to body OAM conversion against PPU."""
import argparse
import hashlib
import json
from pathlib import Path

SIZES=((8,16),(8,32),(8,64),(16,32),(16,64),(32,64),(16,32),(16,32))


def derive(row,origin,obsel,slots):
    inherited=row['object_inherited'] if row['object_inherited']&0x80 else row['global_prop']
    props=row['object_prop']|(inherited&0x30)|(row['object_flags']&0xf0)
    signed=lambda n:n if n<32768 else n-65536
    if len(row['parts'])!=len(slots):raise ValueError('Body piece count mismatch')
    result=[]
    for slot,part in zip(slots,row['parts']):
        large=part['large'];dx=signed(part['dx']);dy=signed(part['dy']);a=part['attr']
        if props&0x40:dx=-dx
        attr=(a&0xc1)^props
        if a&0x20:attr=attr|2 if attr&8 else (attr&0xfb)|8
        result.append({'slot':slot,'x':origin['draw_x']+dx-(8 if large else 4),
                       'y':(origin['draw_y']+origin['draw_z'])%65536+dy-(8 if large else 4),
                       'tile':(part['tile']+row['tile_base'])&255,'size':SIZES[obsel>>5][int(large)],'attr':attr})
    return result


def audit(root,bridge):
    raw=(root/'hair-runtime.jsonl').read_bytes();rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    geometry={r['step']:r for r in rows if r.get('type')=='body_geometry'}
    origins={r['step']:r for r in rows if r.get('type')=='draw_entry' and r['object']==0x1700}
    samples=[]
    for f in bridge['frames']:
        generated=derive(geometry[f['step']],origins[f['step']],f['obsel'],f['body_slots'])
        oam=(root/f"frame-{f['ppu_step']:03d}-oam.bin").read_bytes()
        for p in generated:
            i=p['slot'];x,y,tile,attr=oam[i*4:i*4+4];high=(oam[512+i//4]>>(2*(i%4)))&3
            if high&1:x-=512
            actual={'slot':i,'x':x,'y':y,'tile':tile,'size':SIZES[f['obsel']>>5][high>>1],'attr':attr}
            if p!=actual:raise ValueError(f"OAM mismatch at {f['step']} slot {i}: {p} != {actual}")
        g=geometry[f['step']]
        samples.append({'step':f['step'],'descriptor':f['descriptor'],'parts':len(generated),'object_prop':g['object_prop'],
                        'object_inherited':g['object_inherited'],'object_flags':g['object_flags'],'global_prop':g['global_prop']})
    if not samples:raise ValueError('No samples')
    return {'schema':'issd-actor-oam-properties/v1','capture_sha256':hashlib.sha256(raw).hexdigest(),'samples':samples,
            'limitations':['One actor and direction; position changed in isolated RAM.',
                           'This verifies observed branches only; arbitrary player/team states remain untested.',
                           'Hair OAM, palette and camera origin are not derived here.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('bridge',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.capture,json.loads(a.bridge.read_text(encoding='utf8')));a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Matched {len(r['samples'])} actor property samples")
