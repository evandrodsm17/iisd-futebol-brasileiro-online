"""Audit isolated hair/body draw ranges against same-replay PPU screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from compare_issd_oam_pixels import compose,compare
from compare_issd_replay_oam_frames import audit
from audit_issd_candidate_occlusion import classify


def analyze(root,require_exact=True):
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
    frames=[]; skipped=[]
    for part in hair['frames']:
        parent=bodies.get(part['step'])
        if parent is None or parent['ppu_frame']!=part['ppu_frame']:continue
        if len(part['slots'])!=1 or not parent['slots']:
            skipped.append({'step':part['step'],'reason':'unsupported_candidate_ranges',
                            'hair_slots':len(part['slots']),'body_slots':len(parent['slots'])})
            continue
        ppu=captures[part['ppu_frame']];oam=(root/ppu['oam_ppu']).read_bytes()
        vram=(root/ppu['vram']).read_bytes();cgram=(root/ppu['cgram_ppu']).read_bytes()
        pix=compose(oam,vram,cgram,ppu['obsel'],part['slots']+parent['slots'])
        earlier=compose(oam,vram,cgram,ppu['obsel'],list(range(min(part['slots']+parent['slots']))))
        with Image.open(root/ppu['screenshot']) as image:
            measurement=compare(pix,image)
            occlusion=classify(pix,earlier,image)
        index=part['slots'][0];x,y,tile,attr=oam[index*4:index*4+4]
        frames.append({'step':part['step'],'ppu_frame':part['ppu_frame'],'hair_slot':index,
            'body_slots':parent['slots'],'hair_oam':{'x_low':x,'y':y,'tile':tile,'attr':attr,'palette':(attr>>1)&7},
            'hair_only_pixels':part['candidate_pixels'],'hair_only_mismatches':part['nonmatching_pixels'],
            'body_only_mismatches':parent['nonmatching_pixels'],**measurement,
            'earlier_slot_rgb_matches':occlusion['mismatches_explained_by_earlier_slots'],
            'unexplained_after_earlier_slots':occlusion['unexplained_mismatches']})
    if len(frames)<2:raise ValueError('Insufficient paired frames')
    if require_exact and not any(f['candidate_pixels']>0 and f['nonmatching_pixels']==0 for f in frames):
        raise ValueError('No exact nonempty combined frame')
    return {'schema':'issd-hair-oam-audit/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
        'synthetic_position':positions[0],'frames':frames,'skipped':skipped,'exact_nonempty':sum(f['candidate_pixels']>0 and f['nonmatching_pixels']==0 for f in frames),
        'limitations':['Actor position was changed in RAM in an isolated replay.',
         'Pixel equality only covers selected visible candidate pixels, not hidden parts.',
         'Earlier OAM color matches suggest occlusion but do not prove hardware priority or absence of other effects.',
         'PPU priority, clipping and background interactions are not fully modeled.',
         'One actor, one hair style and one palette do not establish all combinations.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--allow-no-exact',action='store_true',help='Record diagnostic discrepancies; do not treat output as validated')
    a=p.parse_args();result=analyze(a.root,require_exact=not a.allow_no_exact);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Frames: {len(result['frames'])}, exact combined: {result['exact_nonempty']}")
