"""Export local, pixel-checked goalkeeper replay frames; never export the ROM."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from compare_issd_oam_pixels import compose,compare


def export(root,output,report_path):
 output.mkdir(parents=True,exist_ok=True);captures=[]
 for direction in ('Left','Right'):
  folder=root/f'penalty-keeper-visual-{direction.lower()}'
  raw=(folder/'graphics.jsonl').read_bytes();rows=[json.loads(l) for l in raw.splitlines()]
  if rows[0].get('type')!='capture_start' or rows[0].get('direction')!=direction or not rows[0].get('synthetic_players') or rows[-1].get('type')!='capture_end' or rows[-1].get('sequence_count')!=5 or any(e.get('type')=='error' for e in rows):raise ValueError('Incomplete capture')
  if [e['value'] for e in rows if e.get('type')=='selector']!=[28,30,14,16,10]:raise ValueError('Unexpected selector sequence')
  samples=[e for e in rows if e.get('type')=='full_graphics']
  if [e['delta'] for e in samples]!=list(range(1,41)):raise ValueError('Missing frames')
  images={};evidence=[];omitted=[]
  for sample in samples:
   if not all(sample[k] for k in ('vram','oam','cgram','screenshot')):raise ValueError('Missing graphics')
   stem=sample['stem'];oam,vram,cgram=[(folder/f'{stem}-{n}.bin').read_bytes() for n in ('oam','vram','cgram')];candidate=None
   screenshot_path=folder/f'{stem}.png'
   with Image.open(screenshot_path) as screenshot:
    rgb=screenshot.convert('RGB')
    for lag in (1,2,3,4):
     entries=[e for e in rows if e.get('type')=='draw_entry' and e['frame']==sample['frame']-lag]
     matches=[i for i,e in enumerate(entries) if e['object']==0xc00]
     if len(matches)!=1 or matches[0]+1>=len(entries):continue
     i=matches[0];selected=slots(entries[i]['stack'],entries[i+1]['stack'])
     if not selected or any((oam[4*j+3]&0xbf)!=0x3a for j in selected):continue
     pixels=compose(oam,vram,cgram,sample['obsel'],selected)
     mismatch={point for point,color in pixels.items() if rgb.getpixel(point)!=color}
     other=compose(oam,vram,cgram,sample['obsel'],[slot for slot in range(128) if slot not in selected])
     explained={point for point in mismatch if other.get(point)==rgb.getpixel(point)}
     if len(pixels)>=50 and mismatch==explained:
      check=compare(pixels,screenshot)
      candidate=(pixels,{'delta':sample['delta'],'capture_frame':sample['frame'],'draw_frame':sample['frame']-lag,
       'slots':selected,'pixels':len(pixels),'direct_matches':check['exact_rgb_matches'],'overlap_matches':len(explained),
       'screenshot_sha256':hashlib.sha256(screenshot_path.read_bytes()).hexdigest()})
      break
   if candidate is None:omitted.append(sample['delta']);continue
   images[sample['delta']]=candidate[0];evidence.append(candidate[1])
  if len(images)!=39 or omitted!=[1]:raise ValueError(f'Unexpected evidence coverage: {direction}')
  points=[point for pixels in images.values() for point in pixels];left=min(x for x,y in points);right=max(x for x,y in points)+1;top=min(y for x,y in points);bottom=max(y for x,y in points)+1
  width,height=right-left,bottom-top;sheet=Image.new('RGBA',(width*40,height))
  for delta,pixels in images.items():
   for (x,y),color in pixels.items():sheet.putpixel(((delta-1)*width+x-left,y-top),(*color,255))
  name=f'penalty-keeper-synthetic-{direction.lower()}-local.png';path=output/name;sheet.save(path)
  captures.append({'direction':direction,'graphics_sha256':hashlib.sha256(raw).hexdigest(),'atlas':name,
   'atlas_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':width,'height':height,'x':left,'y':top,
   'frames':[n in images for n in range(1,41)],'evidence':evidence,'omitted_deltas':omitted})
 manifest={'schema':'issd-penalty-keeper-synthetic-preview/v1','frame_count':40,'captures':captures,
  'limits':['Player count changed synthetically from 0 to 4; natural two-player setup is unverified.',
            'Two chosen P2 action windows and periodic P1 action pulses; one shared saved state.',
            'The first frame is omitted; matched overlaps do not prove sprite priority.',
            'A 40-frame excerpt and one appearance, not a complete or general goalkeeper animation.',
            'ROM, screenshots, raw graphics and generated images remain local.']}
 (output/'penalty-keeper-synthetic-local.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 report_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 return captures

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
 captures=export(a.root,a.output,a.report)
 print('OK: pixel-checked goalkeeper frames',[(c['direction'],sum(c['frames'])) for c in captures])
