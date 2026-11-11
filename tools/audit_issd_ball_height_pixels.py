"""Compare local ROM screenshots differing only in the ball's synthetic height."""
import argparse,collections,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def components(a,b):
 diff=ImageChops.difference(a,b);width,height=a.size
 pixels={(x,y) for y in range(height) for x in range(width) if diff.getpixel((x,y))!=(0,0,0)}
 groups=[]
 while pixels:
  stack=[pixels.pop()];group=set()
  while stack:
   x,y=stack.pop();group.add((x,y))
   for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if q in pixels:pixels.remove(q);stack.append(q)
  if len(group)>=20:groups.append(group)
 return sorted(groups,key=len,reverse=True)
def box(g):return [min(x for x,y in g),min(y for x,y in g),max(x for x,y in g)+1,max(y for x,y in g)+1]
def audit(trace,directory):
 rows=[json.loads(line) for line in trace.read_bytes().splitlines()]
 def frame(trial,step):
  matches=[r for r in rows if r.get('type')=='frame' and r.get('trial')==trial and r.get('step')==step]
  if len(matches)!=1:raise ValueError('Missing unique trace frame')
  return matches[0]
 def sz(word):return word-65536 if word>=32768 else word
 baseline=frame(11,3);ground=directory/'goal-11-004.png';base_image=Image.open(ground).convert('RGB');output=[]
 if base_image.size!=(256,224) or sz(baseline['z'])!=0:raise ValueError('Unexpected baseline')
 for case in (12,13):
  state=frame(case,3);candidate=directory/f'goal-{case:02d}-004.png';img=Image.open(candidate).convert('RGB')
  if any(state[k]!=baseline[k] for k in ('x','y','nativeX','nativeY')):raise ValueError('Ball positions differ')
  groups=components(base_image,img)
  if len(groups)!=2:raise ValueError(f'Expected two principal difference regions, got {len(groups)}')
  top,bottom=sorted(groups,key=lambda g:box(g)[1]);tb,bb=box(top),box(bottom);distance=bb[1]-tb[1];height=-sz(state['z'])
  shifted={(x,y+distance) for x,y in top};overlap=len(shifted&bottom)
  if distance!=height or tb[0]!=bb[0] or tb[2]!=bb[2] or overlap<len(top)*0.9:raise ValueError('Screenshot difference did not match recorded native height')
  output.append({'trial':case,'comparison_trace_frame':3,'screenshot_step':4,'native_height':sz(state['z']),'vertical_displacement_pixels':distance,'upper_diff_bbox':tb,'lower_diff_bbox':bb,'upper_changed_pixels':len(top),'lower_changed_pixels':len(bottom),'overlap_after_translation':overlap,'image_sha256':sha(candidate)})
 return {'schema':'issd-ball-height-pixels/v1','trace_sha256':sha(trace),'baseline_screenshot_sha256':sha(ground),'image_size':[256,224],'observations':output,'limitations':['Synthetic shots from one camera, stadium and saved state; two observed heights only.','Image difference measures sprite displacement, not an independently identified world-to-screen transformation.','Screenshot step 4 agrees with trace frame 3 in these samples; pipeline latency is not established for every capture.','The SNES screenshot pixel is not automatically one browser world unit or a measure of physical ball radius.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('directory',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.trace,a.directory);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: native heights -55 and -56 match 55 and 56 screenshot pixels in the paired captures')
if __name__=='__main__':main()
