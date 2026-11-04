"""Export three pass body directions only after paired ROM/PPU/pixel validation."""
import argparse,base64,hashlib,json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive,SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_action_trials import load,compare as compare_trials
from compare_issd_oam_pixels import compose,compare as compare_pixels
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def lines(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def export(root,control_root,rom_path,state,output,diagonals=None,detail_report=None):
 rom=rom_path.read_bytes()
 if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 cycles={};evidence={};palette=None;extra_palette=None
 if detail_report:
  report=json.loads(detail_report.read_text(encoding='utf-8'))
  if report.get('schema')!='issd-pass-detail-variants/v1' or report.get('rom_sha256')!=hashlib.sha256(rom).hexdigest() or set(report.get('cases',{}))!={'natural','0','14','30'}:raise ValueError('Detail evidence incompatible')
 cases=[('Up',0,6),('Right',2,0),('DownRight',3,1),('Down',4,2),('DownLeft',5,3),('Left',6,4)]
 if diagonals:cases.extend([('UpRight',1,7),('UpLeft',7,5)])
 for name,screen,direction in cases:
  folder=(diagonals/'A'/name if name in ('UpRight','UpLeft') else root/name);controls=(diagonals/'neutral'/name if name in ('UpRight','UpLeft') else control_root/name);ap=list(folder.glob('issd-auto-probe-*.jsonl'));np=list(controls.glob('issd-auto-probe-*.jsonl'))
  if len(ap)!=1 or len(np)!=1:raise ValueError('Missing replay pair')
  trial=load(ap[0]);neutral=load(np[0]);comparison=compare_trials(trial,neutral,0x8000)
  if not all(comparison[k] for k in ('baseline_matches_observed_fields','extended_fields_compared','p2_action_input_confirmed','p2_control_neutral_in_action_window')):raise ValueError('Unverified replay pair')
  previous=trial['samples'][478];first=trial['samples'][480]
  actor=next(a for a in first['actors'] if a['address']==0x1900)
  if previous['link_a6']!=0x1900 or actor['state']!=0x258 or actor['script']!=0xd01f or actor['direction']!=direction:raise ValueError('Not the expected controlled possession/action')
  draws=lines(folder/'slide-draw.jsonl');captures={x['frame']:x for x in lines(folder/'slide-poses.jsonl')};frames=[];samples=[]
  if any(captures[f]['script']!=0xd01f or captures[f]['descriptor']!=captures[4276 if f<4278 else 4278]['descriptor'] for f in range(4276,4294)) or captures[4294]['script']==0xd01f:raise ValueError('Timing interrupted or not observed')
  for f in (4276,4278):
   g=next(r for r in draws if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==0x1900)
   entries=[r for r in draws if not r.get('type') and r['frame']==f-1];idx=next(i for i,r in enumerate(entries) if r['object']==0x1900)
   candidate=slots(entries[idx]['stack'],entries[idx+1]['stack']);prepared=captures[f];shown=captures[f+1]
   if g['source']!='rom88' or g['parts']!=rom_parts(rom,g['pose']) or g['descriptor']!=prepared['descriptor']:raise ValueError('Geometry mismatch')
   pieces=derive(g,g,prepared['obsel'],candidate)
   if any(((p['attr']>>1)&7) not in (1,5) for p in pieces):raise ValueError('Unvalidated palette bank')
   mirror=(folder/(prepared['stem']+'-mirror.bin')).read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
   ppu=(folder/(shown['stem']+'-ppu.bin')).read_bytes();vram=(folder/(shown['stem']+'-vram.bin')).read_bytes();cgram=(folder/(shown['stem']+'-ppu-cgram.bin')).read_bytes()
   def actual(buf,p):
    i=p['slot'];x,y,tile,attr=buf[i*4:i*4+4];high=(buf[512+i//4]>>(2*(i%4)))&3
    if high&1:x-=512
    return {'slot':i,'x':x,'y':y,'tile':tile,'attr':attr,'size':SIZES[prepared['obsel']>>5][int(bool(high&2))]}
   if any(p!=actual(mirror,p) or p!=actual(ppu,p) for p in pieces):raise ValueError('OAM mismatch')
   pixels=compose(ppu,vram,cgram,shown['obsel'],candidate)
   with Image.open(folder/(shown['stem']+'-screen.png')) as image:
    quality=compare_pixels(pixels,image);image=image.convert('RGB')
    differences=[xy for xy,rgb in pixels.items() if image.getpixel(xy)!=rgb]
    full=compose(ppu,vram,cgram,shown['obsel'],list(range(128)))
    covered=sum(full.get(xy)==image.getpixel(xy) for xy in differences)
   if not quality['candidate_pixels'] or covered!=len(differences):raise ValueError('Screenshot discrepancy not explained by full OAM')
   colors=[int.from_bytes(cgram[(144+i)*2:(145+i)*2],'little') for i in range(16)]
   if palette is not None and colors!=palette:raise ValueError('Palette mismatch')
   palette=colors
   detail_colors=[int.from_bytes(cgram[(208+i)*2:(209+i)*2],'little') for i in range(16)]
   if extra_palette is not None and detail_colors!=extra_palette:raise ValueError('Detail palette mismatch')
   extra_palette=detail_colors;tiles,_=descriptor_tiles(rom,g['descriptor']);tiles=bytearray(tiles);base=g['tile_base']&255;detail_offsets=[]
   for part in g['parts']:
    size=16 if part['large'] else 8
    for y in range(size//8):
     for x in range(size//8):
      tile=part['tile']+x+16*y;address=(((shown['obsel']&7)<<9)+(((shown['obsel']&0x18)+8)<<5)+((base+tile)&255))&2047
      if tile>=24:raise ValueError('Invalid tile')
      actual_tile=vram[address*32:address*32+32]
      if tile==23 and actual_tile!=tiles[tile*32:tile*32+32]:
       offset=rom.find(actual_tile)
       if offset<0:raise ValueError('Detail tile not present in ROM')
       detail_offsets.append(offset)
       tiles[tile*32:tile*32+32]=rom[offset:offset+32]
      if actual_tile!=tiles[tile*32:tile*32+32]:raise ValueError(f'ROM tile mismatch {name} frame {f} tile {tile}')
   inherited=g['object_inherited'] if g['object_inherited']&0x80 else g['global_prop'];props=g['object_prop']|(inherited&0x30)|(g['object_flags']&0xf0)
   frame={'descriptor':g['descriptor'],'props':props,'origin_x':48,'origin_y':68,'parts':g['parts'],'tiles':base64.b64encode(tiles).decode('ascii')}
   if screen==0 and detail_report:
    variants=[]
    for number in range(1,21):
     actor={'type':6,'kit_variant':(number-1)*2,'uniform_selector':4,'object_flags':g['object_flags']}
     detail,meta=descriptor_tiles(rom,g['descriptor'],actor)
     if meta['detail']!=4:raise ValueError('Unexpected descriptor detail')
     variants.append(base64.b64encode(detail[23*32:24*32]).decode('ascii'))
    if base64.b64decode(variants[9])!=tiles[23*32:24*32]:raise ValueError('Captured shirt detail mismatch')
    frame['detail_variants']=variants
   frames.append(frame)
   samples.append({'frame':f,'descriptor':g['descriptor'],'parts':len(pieces),'pixels':quality['candidate_pixels'],'visible_pixels_matching':quality['exact_rgb_matches'],'pixels_covered_by_other_oam':covered,'detail_first_matching_rom_file_offsets':detail_offsets})
  cycles[str(screen)]={'width':96,'height':96,'ticks':[2,16],'frames':frames}
  evidence[name]={'screen_direction':screen,'rom_direction':direction,'baseline_samples':comparison['before_compared'],'trace_sha256':trial['sha256'],'neutral_sha256':neutral['sha256'],'samples':samples}
 output.parent.mkdir(parents=True,exist_ok=True)
 data={'schema':'issd-pass-body-local/v2','rom_sha256':hashlib.sha256(rom).hexdigest(),'team':2,'kit':'home','skin':0,'hair':0,'palette':palette,'extra_palette':extra_palette,'cycles':cycles,'limitations':['One captured actor and team palette; hair association and contexts remain provisional.','ROM-derived graphics remain local.']}
 output.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
 return {'schema':'issd-pass-orientations/v1','rom_sha256':data['rom_sha256'],'declared_state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),'detail_evidence_sha256':hashlib.sha256(detail_report.read_bytes()).hexdigest() if detail_report else None,'cases':evidence,'limitations':['One actor, one savestate, one team palette and configuration.','Some pixels are covered by other OAM objects, confirmed against the full OAM composite; upper diagonals require the optional separately paired capture.','Hair and all match contexts remain unvalidated; local extraction required. Detail offsets are first byte matches, not proof of the actual DMA source.']}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--controls',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--diagonals',type=Path);p.add_argument('--detail-evidence',type=Path)
 a=p.parse_args();r=export(a.root,a.controls,a.rom,a.state,a.output,a.diagonals,a.detail_evidence);a.report.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('validated directions:',len(r['cases']))
