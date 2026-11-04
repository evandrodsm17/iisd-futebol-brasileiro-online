"""Audit synthetic auxiliary hairstyles during the captured normal B action."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from compare_issd_action_trials import load,signature
from compare_issd_oam_pixels import compose,compare
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import lorom_offset
from render_issd_descriptor_sprite import descriptor_tiles


def read(p):return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(root,rom_path,state):
 rom=rom_path.read_bytes()
 if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 cases={};baseline=None
 for style in (1,2,13):
  folder=root/f'replay-{style}';paths=list(folder.glob('issd-auto-probe-*.jsonl'))
  if len(paths)!=1:raise ValueError('Missing replay trace')
  records=read(paths[0]);marker=[r for r in records if r.get('type')=='synthetic_pass_hair']
  if len(marker)!=1 or marker[0]['style']!=style or marker[0]['context']!=0xaa0 or marker[0]['actor']!=0x1900:raise ValueError('Missing synthetic context assignment')
  trial=load(paths[0]);before=[i for i in sorted(trial['samples']) if 0<=i<480]
  if len(before)<240:raise ValueError('Missing baseline')
  if baseline is None:baseline=trial
  elif any(signature(trial['samples'][i],True)!=signature(baseline['samples'][i],True) for i in before):raise ValueError('Logged baseline mismatch')
  if trial['samples'][478]['link_a6']!=0x1900 or any(not trial['samples'][i]['held_p2']&0x8000 for i in range(480,486)):raise ValueError('Missing possession or button')
  draws=read(folder/'slide-draw.jsonl');captures={r['frame']:r for r in read(folder/'slide-poses.jsonl')};frames=[]
  for f in (4276,4278):
   g=next(r for r in draws if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==0x1900)
   aux=[r for r in draws if r.get('type')=='aux_execution' and r['frame']==f-1 and r['context']==0xaa0 and r['parent_y']==0x1900]
   if len(aux)!=1 or aux[0]['parent_desc']!=g['descriptor'] or aux[0]['hair_offset']!=(style-1)*4:raise ValueError('Incorrect auxiliary state')
   entries=[r for r in draws if not r.get('type') and r['frame']==f-1]
   indices={obj:next(i for i,r in enumerate(entries) if r['object']==obj) for obj in (0xaa0,0x1900)}
   hair_slots=slots(entries[indices[0xaa0]]['stack'],entries[indices[0xaa0]+1]['stack']);body_slots=slots(entries[indices[0x1900]]['stack'],entries[indices[0x1900]+1]['stack'])
   if len(hair_slots)!=1 or not body_slots or hair_slots[0]>=min(body_slots):raise ValueError('Unvalidated layering')
   shown=captures[f+1];stem=shown['stem'];ppu=(folder/(stem+'-ppu.bin')).read_bytes();vram=(folder/(stem+'-vram.bin')).read_bytes();cgram=(folder/(stem+'-ppu-cgram.bin')).read_bytes()
   slot=hair_slots[0];x,y,tile,attr=ppu[4*slot:4*slot+4];high=(ppu[512+slot//4]>>(2*(slot%4)))&3
   if high!=0 or (attr>>1)&7!=1:raise ValueError('Unvalidated hair OAM properties')
   _,meta=descriptor_tiles(rom,g['descriptor']);selector=meta['auxiliary_selector']
   pointer=int.from_bytes(rom[0xed6d+(style-1)*4:0xed70+(style-1)*4],'little');offset=lorom_offset(pointer)+(selector-1)*32
   expected=rom[offset:offset+32];base=((shown['obsel']&7)<<9)+((((shown['obsel']&0x18)+8)<<5) if attr&1 else 0);address=((base+tile)&2047)*32
   if vram[address:address+32]!=expected:raise ValueError('Hair tile differs from ROM')
   allslots=hair_slots+body_slots;pixels=compose(ppu,vram,cgram,shown['obsel'],allslots);full=compose(ppu,vram,cgram,shown['obsel'],list(range(128)))
   with Image.open(folder/(stem+'-screen.png')) as image:
    quality=compare(pixels,image);image=image.convert('RGB');mismatch=[xy for xy,rgb in pixels.items() if image.getpixel(xy)!=rgb];covered=sum(full.get(xy)==image.getpixel(xy) for xy in mismatch)
   if not quality['candidate_pixels'] or covered!=len(mismatch):raise ValueError('Unexplained composite mismatch')
   origin_y=(g['draw_y']+g['draw_z'])&65535
   frames.append({'frame':f,'descriptor':g['descriptor'],'selector':selector,'rom_address':pointer,'rom_file_offset':offset,'relative_x':x-g['draw_x'],'relative_y':y-origin_y,'attr':attr,'slot':slot,'body_slots':body_slots,'tile_sha256':hashlib.sha256(expected).hexdigest(),'composite_pixels':quality['candidate_pixels'],'covered_pixels':covered})
  cases[str(style)]={'trace_sha256':trial['sha256'],'draw_sha256':sha(folder/'slide-draw.jsonl'),'synthetic_context':marker[0],'frames':frames}
 return {'schema':'issd-pass-hair-synthetic/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),'actor':0x1900,'screen_direction':2,'cases':cases,'limitations':['A pre-existing auxiliary context was reassigned synthetically in isolated RAM, replacing its previous parent.','One actor, team, skin, direction and two pass frames; other directions are not validated.','Composited visible pixels match or are explained by full OAM; hidden pixels and general PPU priority are not proven.','Team/skin and gameplay context variations are extrapolations.','ROM and captured image data remain local.']}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('validated pass hair styles:',len(r['cases']))
