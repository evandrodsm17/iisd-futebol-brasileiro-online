"""Audit slide ROM geometry, OAM timing, and a paired overlay control."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive, SIZES
from compare_issd_action_trials import load, signature, has_extended
from compare_issd_oam_pixels import compose
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import span


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def rom_parts(rom, pose):
    count=span(rom,0x880000|pose,1)[0]
    data=span(rom,0x880000|pose,1+4*count)
    signed=lambda x: x if x<128 else x+0xff00
    return [{'dx':signed(data[2+4*i]),'dy':signed(data[1+4*i]),
             'tile':data[3+4*i],'attr':data[4+4*i],
             'large':bool(data[4+4*i]&0x10)} for i in range(count)]


def one_trace(root):
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1: raise ValueError('Expected one replay trace')
    return load(paths[0])


def audit(root,control,rom_path,state):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    a,n=one_trace(root),one_trace(control);common=set(a['samples'])&set(n['samples'])
    before=sorted(t for t in common if 0<=t<480)
    if not (any(set(range(i,480,2))<=set(before) for i in (0,1)) and
            all(has_extended(x['samples'][t]) for x in (a,n) for t in before) and
            all(signature(a['samples'][t],True)==signature(n['samples'][t],True) for t in before) and
            all(a['samples'][t]['held_p1']==0x80 and n['samples'][t]['held_p1']==0 for t in range(480,486))):
        raise ValueError('Baseline or input mismatch')
    draw_path=root/'slide-draw.jsonl';data=[json.loads(x) for x in draw_path.read_text().splitlines() if x.strip()]
    poses={r['frame']:r for r in (json.loads(x) for x in (root/'slide-poses.jsonl').read_text().splitlines() if x.strip())}
    controls={r['frame']:r for r in (json.loads(x) for x in (control/'overlay-control.jsonl').read_text().splitlines() if x.strip())}
    actor=a['samples'][479]['selected_p1'];frames=[]
    for t in (480,482,484,495,500,505):
        sample=a['samples'][t]; f=sample['frame']; capture=poses[f]; displayed=poses[f+1]
        events=[r for r in data if not r.get('type') and r['frame']==f-1]
        indexes=[i for i,r in enumerate(events) if r['object']==actor]
        geometry=[r for r in data if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==actor]
        if len(indexes)!=1 or indexes[0]+1>=len(events) or len(geometry)!=1: raise ValueError('Draw record missing')
        g=geometry[0];i=indexes[0];candidate=slots(events[i]['stack'],events[i+1]['stack'])
        if g['source']!='rom88' or g['descriptor']!=capture['descriptor'] or g['pose']!=capture['pose'] or g['parts']!=rom_parts(rom,g['pose']):
            raise ValueError('ROM geometry mismatch')
        if len(candidate)!=len(g['parts']): raise ValueError('Geometry and draw count differ')
        expected=derive(g,g,capture['obsel'],candidate)
        mirror=(root/(capture['stem']+'-mirror.bin')).read_bytes(); mirror=mirror[:512][::-1]+mirror[512:]
        ppu_path=root/(displayed['stem']+'-ppu.bin');ppu=ppu_path.read_bytes()
        def actual(o,part):
            slot=part['slot'];x,y,tile,attr=o[slot*4:slot*4+4];high=(o[512+slot//4]>>(2*(slot%4)))&3
            if high&1: x-=512
            return {'slot':slot,'x':x,'y':y,'tile':tile,'attr':attr,'size':SIZES[capture['obsel']>>5][int(bool(high&2))]}
        if any(part!=actual(mirror,part) or part!=actual(ppu,part) for part in expected):
            raise ValueError(f'OAM geometry mismatch at frame {f}')
        vram=root/(displayed['stem']+'-vram.bin'); cgram=root/(displayed['stem']+'-ppu-cgram.bin')
        shot=root/(displayed['stem']+'-screen.png');control_capture=controls[f+1]
        if not control_capture['success']: raise ValueError('Control screenshot failed')
        control_shot=control/control_capture['screenshot']
        pixels=compose(ppu,vram.read_bytes(),cgram.read_bytes(),displayed['obsel'],candidate)
        with Image.open(shot) as image, Image.open(control_shot) as ref:
            if image.size!=(256,224) or ref.size!=(256,224): raise ValueError('Unexpected screenshot size')
            image=image.convert('RGB');ref=ref.convert('RGB')
            mismatch=[(xy,image.getpixel(xy),ref.getpixel(xy)) for xy,rgb in pixels.items() if image.getpixel(xy)!=rgb]
        frames.append({'elapsed':t,'draw_frame':f-1,'prepared_frame':f,'displayed_frame':f+1,
                       'descriptor':capture['descriptor'],'pose':g['pose'],'slots':candidate,
                       'parts':len(expected),'rom_geometry_matches':True,'mirror_and_ppu_match':True,
                       'candidate_pixels':len(pixels),'direct_mismatches':len(mismatch),
                       'same_as_control':sum(a==b for _,a,b in mismatch),
                       'mismatch_positions':[list(xy) for xy,_,_ in mismatch],
                       'displayed_oam_sha256':sha(ppu_path),'screenshot_sha256':sha(shot),
                       'control_screenshot_sha256':sha(control_shot)})
    return {'schema':'issd-slide-timing-geometry/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'declared_state_sha256':sha(state),'trace_sha256':a['sha256'],'control_trace_sha256':n['sha256'],
            'draw_sha256':sha(draw_path),'baseline_samples':len(before),'actor':actor,'frames':frames,
            'limitations':['Observed timing applies to this core and replay; do not assume all emulators share it.',
                           'A shared white pixel suggests an overlay but does not prove the PPU layer.',
                           'Body geometry coverage does not prove auxiliary hair or other separate objects are included.',
                           'One actor, one direction and one scenario; gameplay effects are not validated.',
                           'ROM and image captures remain local; no spritesheet is produced.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.control,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('poses:',len(r['frames']),'parts:',sum(f['parts'] for f in r['frames']),
          'mismatches:',sum(f['direct_mismatches'] for f in r['frames']),
          'same in control:',sum(f['same_as_control'] for f in r['frames']))
