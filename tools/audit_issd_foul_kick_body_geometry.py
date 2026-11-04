"""Validate foul-kick body geometry against OAM and native screenshots."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive,SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_oam_pixels import compose,compare
from extract_issd_catalog import EXPECTED_MD5


def read(p):return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(root,reference,rom_path,state):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    draws=read(root/'slide-draw.jsonl');captures={r['frame']:r for r in read(root/'slide-poses.jsonl')}
    manifests=list(reference.glob('*-graphics.jsonl'))
    if len(manifests)!=1:raise ValueError('Missing previous capture')
    previous={r['frame']:r for r in read(manifests[0])}
    samples=[]
    for f in (4596,4600,4603,4606,4607,4610,4611,4612,4613):
        events=[r for r in draws if not r.get('type') and r['frame']==f-1]
        found=[i for i,r in enumerate(events) if r['object']==0x1200]
        geometry=[r for r in draws if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==0x1200]
        if len(found)!=1 or found[0]+1>=len(events) or len(geometry)!=1:raise ValueError('Missing draw event')
        g=geometry[0];idx=found[0];candidate=slots(events[idx]['stack'],events[idx+1]['stack']);prepared=captures[f];shown=captures[f+1]
        if g['descriptor']!=prepared['descriptor'] or g['pose']!=prepared['pose'] or previous[f]['actor']['descriptor']!=prepared['descriptor']:
            raise ValueError('Inconsistent descriptor')
        if g['source']=='rom88' and g['parts']!=rom_parts(rom,g['pose']):raise ValueError('ROM geometry differs')
        pieces=derive(g,g,prepared['obsel'],candidate)
        mirror=(root/(prepared['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
        ppu_path=root/(shown['stem']+'-ppu.bin');ppu=ppu_path.read_bytes()
        def actual(o,part):
            slot=part['slot'];x,y,tile,attr=o[slot*4:slot*4+4];high=(o[512+slot//4]>>(2*(slot%4)))&3
            if high&1:x-=512
            return {'slot':slot,'x':x,'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][int(bool(high&2))]}
        mirror_mismatch=sum(x!=actual(mirror,x) for x in pieces);ppu_mismatch=sum(x!=actual(ppu,x) for x in pieces)
        if mirror_mismatch:raise ValueError('Mirror mismatch')
        if f!=4613 and ppu_mismatch:raise ValueError('Unexpected PPU mismatch')
        if f==4613 and not ppu_mismatch:raise ValueError('Direction-change timing needs re-evaluation')
        pixels=compose(ppu,(root/(shown['stem']+'-vram.bin')).read_bytes(),(root/(shown['stem']+'-ppu-cgram.bin')).read_bytes(),shown['obsel'],candidate)
        with Image.open(root/(shown['stem']+'-screen.png')) as image:comparison=compare(pixels,image)
        if f!=4613 and (comparison['nonmatching_pixels'] or not comparison['candidate_pixels']):raise ValueError('Screenshot mismatch')
        samples.append({'draw_frame':f-1,'prepared_frame':f,'displayed_frame':f+1,'descriptor':g['descriptor'],
          'source':g['source'],'pose':g['pose'],'slots':candidate,'parts':len(pieces),'mirror_mismatches':mirror_mismatch,
          'ppu_mismatches':ppu_mismatch,'pixels':comparison,'ppu_sha256':sha(ppu_path)})
    return {'schema':'issd-foul-kick-body-geometry/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),
      'draw_sha256':sha(root/'slide-draw.jsonl'),'reference_graphics_sha256':sha(manifests[0]),'actor':0x1200,'frames':samples,
      'limitations':['One actor and one controlled A-button foul under synthetic referee and foul settings.',
       'Body slots validated; separate hair and auxiliary objects are not covered.',
       'WRAM-derived layouts match OAM but have not been proven equivalent to direct ROM geometry.',
       'At prepared frame 4613, after the direction change, all six pieces disagree with the next PPU sample; timing remains unresolved.',
       'Matching screenshot pixels validates visible body candidate pixels, not hidden or occluded pixels and not general PPU priority.',
       'Raw assets and ROM remain local.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--reference',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root,a.reference,a.rom,a.state);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('validated body samples:',len(result['frames'])-1,'direction-change sample remains unresolved')
