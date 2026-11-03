"""Check replay-backed relative geometry and attributes against captured OAM."""
import argparse
import hashlib
import json
from pathlib import Path
from export_issd_team_motion import trace
from render_issd_descriptor_sprite import normalise_parts


def audit(root,trace_path,hair_audit):
    bridge=json.loads((root/'descriptor-bridge.json').read_text(encoding='utf8'))
    rows=[json.loads(line) for line in (root/'hair-runtime.jsonl').read_text(encoding='utf8').splitlines()]
    draw={(r['step'],r['object']):r for r in rows if r.get('type')=='draw_entry'}
    actors={}
    for sample in trace(trace_path):
        for actor in sample.get('actors',[]):
            if actor['address']==0x0d00 and actor['direction']==4:actors.setdefault(actor['descriptor'],actor)
    heads={r['descriptor']:r for r in hair_audit['frames']};frames=[]
    for f in bridge['frames']:
        origin=draw[(f['step'],0x1700)];ox=origin['draw_x'];oy=(origin['draw_y']+origin['draw_z'])%65536
        parts=normalise_parts(actors[f['descriptor']]['parts']);oam=(root/f"frame-{f['ppu_step']:03d}-oam.bin").read_bytes()
        if len(parts)!=len(f['body_slots']):raise ValueError('Piece count mismatch')
        masks=set()
        for p,slot in zip(parts,f['body_slots']):
            x,y,tile,attr=oam[slot*4:slot*4+4];high=(oam[512+slot//4]>>(2*(slot%4)))&3
            if high&1:x-=512
            size=((8,16),(8,32),(8,64),(16,32),(16,64),(32,64),(16,32),(16,32))[f['obsel']>>5][high>>1]
            if (x,y,tile,size)!=(ox+p['x'],oy+p['y'],(f['base_tile']+p['tile'])&255,p['size']):raise ValueError(f"Body geometry mismatch {f['step']}")
            masks.add(p['attr']^attr)
        if len(masks)!=1:raise ValueError('Inconsistent attributes')
        h=heads[f['descriptor']];slot=f['hair_slot'];x,y,tile,attr=oam[slot*4:slot*4+4]
        high=(oam[512+slot//4]>>(2*(slot%4)))&3
        if high&1:x-=512
        if high&2 or (x,y)!=(ox+h['hair_x'],oy+h['hair_y']):raise ValueError(f"Hair geometry mismatch {f['step']}")
        frames.append({'step':f['step'],'descriptor':f['descriptor'],'body_parts':len(parts),
                       'attribute_xor':masks.pop(),'hair_slot':slot,'hair_tile':tile,'hair_attr':attr})
    if not frames:raise ValueError('No matching geometry')
    return {'schema':'issd-relative-oam-geometry/v1','trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),
            'capture_sha256':hashlib.sha256((root/'hair-runtime.jsonl').read_bytes()).hexdigest(),'frames':frames,
            'limitations':['Relative body geometry comes from a different trace, hair geometry from the replay audit.',
                           'Attribute XOR, OAM slots, hair tile and palette are captured context, not generalized actor state.',
                           'One actor and direction; the actor position was synthetic.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('trace',type=Path);p.add_argument('hair_audit',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.capture,a.trace,json.loads(a.hair_audit.read_text(encoding='utf8')));a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print(f"Matched relative OAM geometry in {len(r['frames'])} samples")
