"""Validate and export the captured ball-holder jump as local OAM compositions."""
import argparse, base64, hashlib, json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive, SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_action_trials import load, signature, has_extended
from compare_issd_oam_pixels import compose
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]
def trace(root):
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1:raise ValueError('Expected one trace')
    if not any(r.get('type')=='session_end' and r.get('experiment_triggered') for r in read(paths[0])):raise ValueError('Incomplete capture')
    return load(paths[0])
def encode(data):return base64.b64encode(data).decode('ascii')

def export(root,control,rom_path,state, start_elapsed=426, expected=None, direction=4, allow_oam_occlusion=False):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    a,n=trace(root),trace(control);before=sorted(t for t in set(a['samples'])&set(n['samples']) if t<420)
    if not any(set(range(i,410,2))<=set(before) for i in (0,1)) or any(not has_extended(a['samples'][t]) or not has_extended(n['samples'][t]) or signature(a['samples'][t],True)!=signature(n['samples'][t],True) for t in before):raise ValueError('Baseline differs')
    if any(a['samples'][t]['held_p1']!=0x80 or n['samples'][t]['held_p1']!=0 for t in range(420,426)):raise ValueError('Action pair mismatch')
    events=read(root/'slide-draw.jsonl');captures={r['frame']:r for r in read(root/'slide-poses.jsonl')};actor=0x1900;frames=[];report=[];expected_descriptors=[expected[0]]*10+[expected[1]]*8+[expected[2]]*5 if expected else [0xbcd6]*10+[0xbcdf]*8+[0xbce8]*5
    for tick,descriptor in enumerate(expected_descriptors):
        sample=a['samples'][start_elapsed+tick];carrier=next(x for x in sample['actors'] if x['address']==actor)
        if sample['link_a6']!=actor or sample['held_p2']!=0 or carrier['state']!=0x370 or carrier['script']!=0xdf4d or carrier['direction']!=direction or carrier['descriptor']!=descriptor:raise ValueError('Unexpected ball-holder jump state')
        f=sample['frame'];prepared=captures[f];displayed=captures[f+1]
        g=next(r for r in events if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==actor)
        draws=[r for r in events if not r.get('type') and r['frame']==f-1]
        found=[i for i,r in enumerate(draws) if r.get('object')==actor]
        if len(found)!=1 or found[0]+1>=len(draws):raise ValueError('Draw range missing')
        i=found[0];candidate=slots(draws[i]['stack'],draws[i+1]['stack'])
        if g['descriptor']!=descriptor or prepared['descriptor']!=descriptor or g['source']!='rom88' or g['parts']!=rom_parts(rom,g['pose']):raise ValueError('Pose mismatch')
        parts=derive(g,g,prepared['obsel'],candidate);mirror=(root/(prepared['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
        oam=(root/(displayed['stem']+'-ppu.bin')).read_bytes();vram=(root/(displayed['stem']+'-vram.bin')).read_bytes();cgram=(root/(displayed['stem']+'-ppu-cgram.bin')).read_bytes()
        def actual(buf,p):
            slot=p['slot'];x,y,tile,attr=buf[slot*4:slot*4+4];high=(buf[512+slot//4]>>(2*(slot%4)))&3
            return {'slot':slot,'x':x-(512 if high&1 else 0),'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][high>>1]}
        if any(part!=actual(mirror,part) or part!=actual(oam,part) for part in parts):raise ValueError('OAM mismatch')
        source,_=descriptor_tiles(rom,descriptor,{'type':g['actor_type'],'kit_variant':g['kit_variant'],'uniform_selector':g['uniform_selector'],'object_flags':g['object_flags']});base=g['tile_base']&255;used={}
        for part in parts:
            bank=part['attr']&1
            for y in range(part['size']//8):
                for x in range(part['size']//8):
                    tile=(((part['tile']&0xf0)|((part['tile']+x)&15))+16*y)&255;index=(tile-base)&255
                    address=((((prepared['obsel']&7)<<9)+((((prepared['obsel']&0x18)+8)<<5) if bank else 0)+tile)&2047)*32
                    raw=source[index*32:index*32+32]
                    if len(raw)!=32 or raw!=vram[address:address+32]:raise ValueError('ROM tile mismatch')
                    used[address]=raw
        pixels=compose(oam,vram,cgram,displayed['obsel'],candidate)
        with Image.open(root/(displayed['stem']+'-screen.png')) as im:
            im=im.convert('RGB');mismatches={xy:im.getpixel(xy) for xy,rgb in pixels.items() if im.getpixel(xy)!=rgb}
        covered=set();occluders=set()
        if mismatches and allow_oam_occlusion:
            for slot in range(max(candidate)):
                if slot in candidate:continue
                ox,oy,tile,attr=oam[4*slot:4*slot+4]
                if ox==oy==tile==attr==0xf0:continue
                if not any(ox-64<=x<ox+64 and oy-64<=y<oy+64 for x,y in mismatches):continue
                layer=compose(oam,vram,cgram,displayed['obsel'],[slot])
                matching={xy for xy,rgb in mismatches.items() if layer.get(xy)==rgb}
                if matching:covered.update(matching);occluders.add(slot)
        if len(covered)!=len(mismatches):raise ValueError(f'Unexplained screenshot mismatch at {f}: {len(mismatches)-len(covered)}')
        mismatch=len(mismatches)
        for part in parts:
            part['x']+=48-g['draw_x'];part['y']+=68-g['draw_y']
            if part['x']<0 or part['y']<0 or part['x']+part['size']>96 or part['y']+part['size']>96:raise ValueError('Body outside cell')
        frames.append({'descriptor':descriptor,'obsel':displayed['obsel'],'parts':parts,'tiles':[{'address':addr,'data':encode(tile)} for addr,tile in sorted(used.items())],'cgram':encode(cgram)})
        report.append({'tick':tick,'prepared_frame':f,'displayed_frame':f+1,'descriptor':descriptor,'pose':g['pose'],'slots':candidate,'candidate_pixels':len(pixels),'screenshot_mismatches':mismatch,'oam_occluded_pixels':len(covered),'occluder_slots':sorted(occluders),'oam_sha256':sha(root/(displayed['stem']+'-ppu.bin'))})
    local={'schema':'issd-jump-lab-local/v1','width':96,'height':96,'frames':frames,'ticks_per_second':60,'rom_direction':direction,'limitations':['One captured actor and appearance; no hair-layer generalization.','Local ROM-derived resources; do not distribute.']}
    evidence={'schema':'issd-jump-lab-evidence/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),'action_trace_sha256':a['sha256'],'control_trace_sha256':n['sha256'],'draw_sha256':sha(root/'slide-draw.jsonl'),'baseline_samples':len(before),'actor':actor,'rom_direction':direction,'frames':report,'limitations':['One captured actor, direction, context and appearance.','Background priority, hair layers and other OAM objects are not modeled.','Matching logged fields does not prove complete emulator state equality.']}
    return local,evidence

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('control',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--allow-oam-occlusion',action='store_true');p.add_argument('--start-elapsed',type=int,default=426);p.add_argument('--direction',type=int,default=4);p.add_argument('--descriptors',nargs=3,type=lambda x:int(x,0));a=p.parse_args();local,evidence=export(a.root,a.control,a.rom,a.state,a.start_elapsed,a.descriptors,a.direction,a.allow_oam_occlusion)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(local,separators=(',',':')),encoding='utf8');a.evidence.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8');print('OK:',len(local['frames']),'jump frames verified against ROM, OAM, VRAM and screenshot')
