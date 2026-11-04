"""Validate the normal-possession B action body against ROM geometry and PPU."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive,SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_action_trials import load,compare as compare_trials
from compare_issd_oam_pixels import compose,compare as compare_pixels
from extract_issd_catalog import EXPECTED_MD5


def read(p):return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(root,control,rom_path,state):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Wrong ROM revision')
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1:raise ValueError('Expected one input trace')
    trial=load(paths[0]);neutral=load(control);comparison=compare_trials(trial,neutral,0x8000)
    if not all(comparison[k] for k in ('baseline_matches_observed_fields','extended_fields_compared','p2_action_input_confirmed','p2_control_neutral_in_action_window')):
        raise ValueError('Unverified baseline or input')
    draws=read(root/'slide-draw.jsonl');captures={r['frame']:r for r in read(root/'slide-poses.jsonl')}
    frames=[]
    for f,descriptor in ((4276,0xa629),(4278,0xa632)):
        sample=next((r for r in trial['samples'].values() if r['frame']==f),None)
        if not sample:raise ValueError('Missing sample')
        player=next(a for a in sample['actors'] if a['address']==0x1900)
        if sample['input_p2']!='B' or player['state']!=0x258 or player['script']!=0xd01f or player['descriptor']!=descriptor:
            raise ValueError('Unexpected actor action')
        events=[r for r in draws if not r.get('type') and r['frame']==f-1]
        ix=[i for i,r in enumerate(events) if r['object']==0x1900]
        geometry=[r for r in draws if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==0x1900]
        if len(ix)!=1 or ix[0]+1>=len(events) or len(geometry)!=1:raise ValueError('Missing draw event')
        g=geometry[0];prepared=captures[f];displayed=captures[f+1]
        if g['descriptor']!=descriptor or g['pose']!=prepared['pose'] or g['source']!='rom88' or g['parts']!=rom_parts(rom,g['pose']):
            raise ValueError('ROM geometry mismatch')
        candidate=slots(events[ix[0]]['stack'],events[ix[0]+1]['stack']);parts=derive(g,g,prepared['obsel'],candidate)
        mirror=(root/(prepared['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
        ppupath=root/(displayed['stem']+'-ppu.bin');ppu=ppupath.read_bytes()
        def actual(o,part):
            slot=part['slot'];x,y,tile,attr=o[4*slot:4*slot+4];high=(o[512+slot//4]>>(2*(slot%4)))&3
            if high&1:x-=512
            return {'slot':slot,'x':x,'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][int(bool(high&2))]}
        if any(p!=actual(mirror,p) or p!=actual(ppu,p) for p in parts):raise ValueError('OAM mismatch')
        pixels=compose(ppu,(root/(displayed['stem']+'-vram.bin')).read_bytes(),(root/(displayed['stem']+'-ppu-cgram.bin')).read_bytes(),displayed['obsel'],candidate)
        with Image.open(root/(displayed['stem']+'-screen.png')) as image:result=compare_pixels(pixels,image)
        if result['nonmatching_pixels'] or not result['candidate_pixels']:raise ValueError('Visible pixels differ')
        frames.append({'draw_frame':f-1,'prepared_frame':f,'displayed_frame':f+1,'descriptor':descriptor,'pose':g['pose'],
            'slots':candidate,'parts':len(parts),'rom_geometry_matches':True,'mirror_and_ppu_match':True,'pixels':result,'ppu_sha256':sha(ppupath)})
    return {'schema':'issd-normal-b-action-body/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),
        'action_trace_sha256':trial['sha256'],'neutral_trace_sha256':neutral['sha256'],'draw_sha256':sha(root/'slide-draw.jsonl'),
        'baseline_samples':comparison['before_compared'],'controller':2,'button':'B','actor':0x1900,'state':0x258,'script':0xd01f,'frames':frames,
        'limitations':['One normal-possession scenario, one direction and one physical B button with the current game configuration.',
          'The command has not been semantically established as a pass; button mapping can be configured.',
          'Two body frames only; separate hair and other objects are not validated.',
          'Visible candidate pixels match the screenshots; this does not validate occluded pixels or general PPU priority.',
          'Sampled baseline equality does not cover unobserved state; save-state identity is declared.',
          'ROM, screenshots and captured graphics remain local.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--control',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.control,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('normal B action: two ROM body poses validated')
