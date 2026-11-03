"""Audit isolated hair/body draw ranges against same-replay PPU screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from compare_issd_oam_pixels import compose,compare
from compare_issd_replay_oam_frames import audit


def analyze(root):
    trace=root/'hair-runtime.jsonl';raw=trace.read_bytes()
    rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    positions=[r for r in rows if r.get('type')=='synthetic_position']
    if len(positions)!=1 or positions[0]['actor']!=0x1700:
        raise ValueError('Expected documented synthetic actor positioning')
    if not any(r.get('type')=='draw_hook_registration' and r.get('success') for r in rows):raise ValueError('Missing draw hook')
    if not any(r.get('type')=='session_end' and r.get('steps')==120 for r in rows):raise ValueError('Incomplete trace')
    graphics=[]
    for row in rows:
        if row.get('type')!='graphics':continue
        if row['context']!=0x0bd0 or row['parent']!=0x1700 or not row['screenshot']:
            raise ValueError('Unexpected context or screenshot unavailable')
        stem=f"frame-{row['step']:03d}"
        graphics.append({'step':row['step'],'frame':row['frame'],'oam_mirror':stem+'-mirror.bin',
            'oam_ppu':stem+'-oam.bin','vram':stem+'-vram.bin','cgram_ppu':stem+'-cgram.bin',
            'screenshot':stem+'.png','obsel':row['obsel'],
            'actor':{'animation_script':0,'descriptor':row['context_desc'],'direction':0}})
    hair=audit(rows,graphics,root,0x0bd0);body=audit(rows,graphics,root,0x1700)
    bodies={r['step']:r for r in body['frames']};captures={r['frame']:r for r in graphics}
    frames=[]
    for part in hair['frames']:
        parent=bodies.get(part['step'])
        if parent is None or parent['ppu_frame']!=part['ppu_frame']:continue
        if len(part['slots'])!=1 or not parent['slots']:raise ValueError('Unexpected candidate ranges')
        ppu=captures[part['ppu_frame']];oam=(root/ppu['oam_ppu']).read_bytes()
        vram=(root/ppu['vram']).read_bytes();cgram=(root/ppu['cgram_ppu']).read_bytes()
        pix=compose(oam,vram,cgram,ppu['obsel'],part['slots']+parent['slots'])
        with Image.open(root/ppu['screenshot']) as image:measurement=compare(pix,image)
        index=part['slots'][0];x,y,tile,attr=oam[index*4:index*4+4]
        frames.append({'step':part['step'],'ppu_frame':part['ppu_frame'],'hair_slot':index,
            'body_slots':parent['slots'],'hair_oam':{'x_low':x,'y':y,'tile':tile,'attr':attr,'palette':(attr>>1)&7},
            'hair_only_pixels':part['candidate_pixels'],'hair_only_mismatches':part['nonmatching_pixels'],
            'body_only_mismatches':parent['nonmatching_pixels'],**measurement})
    if len(frames)<2 or not any(f['candidate_pixels']>0 and f['nonmatching_pixels']==0 for f in frames):
        raise ValueError('No exact nonempty combined frame')
    return {'schema':'issd-hair-oam-audit/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
        'synthetic_position':positions[0],'frames':frames,'exact_nonempty':sum(f['candidate_pixels']>0 and f['nonmatching_pixels']==0 for f in frames),
        'limitations':['Actor position was changed in RAM in an isolated replay.',
         'Pixel equality only covers selected visible candidate pixels, not hidden parts.',
         'Other frames differ; PPU priority, occlusion and clipping are not fully modeled.',
         'One actor, one hair style and one palette do not establish all combinations.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=analyze(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Frames: {len(result['frames'])}, exact combined: {result['exact_nonempty']}")
