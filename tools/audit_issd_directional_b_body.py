"""Audit directional B action captures against a neutral replay and native OAM."""
import argparse,hashlib,json
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
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    neutral=load(control);results={}
    for direction in ('Up','UpRight','Right','DownRight','Down','DownLeft','Left','UpLeft'):
        directory=root/direction;traces=list(directory.glob('issd-auto-probe-*.jsonl'))
        if len(traces)!=1:raise ValueError('Missing trace')
        trial=load(traces[0]);comparison=compare_trials(trial,neutral,0x8000)
        if not all(comparison[k] for k in ('baseline_matches_observed_fields','extended_fields_compared','p2_action_input_confirmed','p2_control_neutral_in_action_window')):raise ValueError('Baseline mismatch')
        if any(trial['samples'][i]['input_p2']!='B+'+direction for i in range(480,486)):
            raise ValueError('Button or direction missing')
        draws=read(directory/'slide-draw.jsonl');captures={r['frame']:r for r in read(directory/'slide-poses.jsonl')};frames=[];previous=None
        for f in range(4276,4294):
            cap=captures[f];key=(cap['script'],cap['descriptor'],cap['direction'])
            if key==previous:continue
            previous=key
            events=[x for x in draws if not x.get('type') and x['frame']==f-1]
            indices=[i for i,x in enumerate(events) if x['object']==0x1900]
            geometry=[x for x in draws if x.get('type')=='body_geometry' and x['frame']==f-1 and x['object']==0x1900]
            if len(indices)!=1 or len(geometry)!=1 or indices[0]+1>=len(events):raise ValueError('Draw event missing')
            g=geometry[0]
            if g['descriptor']!=cap['descriptor'] or g['pose']!=cap['pose']:raise ValueError('Frame mismatch')
            if g['source']=='rom88' and g['parts']!=rom_parts(rom,g['pose']):raise ValueError('ROM mismatch')
            candidate=slots(events[indices[0]]['stack'],events[indices[0]+1]['stack']);parts=derive(g,g,cap['obsel'],candidate)
            mirror=(directory/(cap['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
            shown=captures[f+1];oam_path=directory/(shown['stem']+'-ppu.bin');oam=oam_path.read_bytes()
            def actual(buf,p):
                i=p['slot'];x,y,tile,attr=buf[i*4:i*4+4];high=(buf[512+i//4]>>(2*(i%4)))&3
                if high&1:x-=512
                return {'slot':i,'x':x,'y':y,'tile':tile,'attr':attr,'size':SIZES[cap['obsel']>>5][int(bool(high&2))]}
            if any(p!=actual(mirror,p) or p!=actual(oam,p) for p in parts):raise ValueError('OAM mismatch')
            pixels=compose(oam,(directory/(shown['stem']+'-vram.bin')).read_bytes(),(directory/(shown['stem']+'-ppu-cgram.bin')).read_bytes(),shown['obsel'],candidate)
            with Image.open(directory/(shown['stem']+'-screen.png')) as im:result=compare_pixels(pixels,im)
            if result['nonmatching_pixels'] or not result['candidate_pixels']:raise ValueError('Pixel mismatch')
            frames.append({'frame':f,'script':key[0],'descriptor':key[1],'direction':key[2],'source':g['source'],
              'parts':len(parts),'slots':candidate,'pixels':result,'ppu_sha256':sha(oam_path)})
        results[direction]={'input':trial['samples'][480]['input_p2'],'held_mask':trial['samples'][480]['held_p2'],
            'baseline_samples':comparison['before_compared'],'trace_sha256':trial['sha256'],'draw_sha256':sha(directory/'slide-draw.jsonl'),'frames':frames}
    return {'schema':'issd-directional-b-body/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),
        'neutral_trace_sha256':neutral['sha256'],'controller':2,'actor':0x1900,'cases':results,
        'limitations':['One savestate, one actor and one configurable control setup; B+direction is not proven to be a normal pass in every context.',
          'Directions are controller directions and not interchangeable with screen or ROM animation directions.',
          'Only distinct body descriptors observed in the chosen frame window are verified; hair and auxiliary objects are excluded.',
          'WRAM geometry matches OAM and screenshot but is not validated directly against ROM.',
          'Logged baseline equality does not establish all hidden state; save-state identity is declared.',
          'ROM and capture assets remain local.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--control',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.control,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('directional B: verified',sum(len(c['frames']) for c in r['cases'].values()),'body frames')
