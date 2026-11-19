"""Verify captured shot input, ROM vector and uninterrupted flight to visual excerpt."""
import hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
rom=Path('International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc').read_bytes()
if hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or rom[0x63d7c:0x63d7f]!=bytes([0x28,0,0x50]) or rom[0xddd8:0xdddd]!=bytes([1,9,8,10,2]):raise ValueError('Unexpected ROM')
motion=json.loads(Path('dist/data/issd-penalty-motion-projection.json').read_text(encoding='utf8'))
results=[]
for cap in motion['captures']:
 folder=Path('analysis/movement-progression-probe')/f"penalty-projection-{cap['input']}-v3"
 raw=(folder/'mode-hooks.jsonl').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=cap['hooks_sha256']:raise ValueError('Unexpected hook trace')
 events=[json.loads(l) for l in raw.splitlines()]
 graphics=(folder/'graphics.jsonl').read_bytes()
 if hashlib.sha256(graphics).hexdigest()!=cap['graphics_sha256']:raise ValueError('Unexpected graphics trace')
 image=next(e for e in map(json.loads,graphics.splitlines()) if e.get('type')=='full_graphics' and e['delta']==2)
 target=image['frame']-2
 shots=[e for e in events if e.get('site')=='penalty_shot_vector' and e['frame']<target and e.get('d')==0x700]
 shot=max(shots,key=lambda e:e['frame'])
 finals=[e for e in events if e.get('site')=='penalty_shot_final' and e.get('frame')==shot['frame'] and all(e[k]==shot[k] for k in ('d','side','round'))]
 if len(finals)!=1:raise ValueError('Ambiguous launch')
 final=finals[0];code=(final['input_word']>>8)&11;table=list(rom[0xddd8:0xdddd]);base=table.index(code) if code in table else 2
 offset=rom[0x63d7c+shot['variant']]+2*base
 if shot['x']!=offset or shot['index']!=base+(0 if shot['flags']&0x10 else 5):raise ValueError('Unexpected direction')
 def signed(at):return int.from_bytes(rom[at:at+2],'little',signed=True)
 vector=[signed(0x63d95+offset),signed(0x63d8b+offset),signed((0x63da9 if shot['flags']&0x10 else 0x63d9f)+offset)]
 state={'x':shot['px'],'y':shot['py'],'z':shot['pz']}
 for name,key,value in zip(('vx','vy','vz'),('dx','dy','dz'),vector):
  observed=shot[key]|shot[key+'_ext']<<16
  if observed!=value&0xffffff:raise ValueError('Vector mismatch')
  state[name]=observed
 initial=state.copy();steps=[]
 for frame in range(shot['frame']+1,target+1):
  current=[e for e in events if e.get('site')=='penalty_shot_step' and e.get('frame')==frame and all(e[k]==shot[k] for k in ('d','side','round'))]
  if len(current)!=1:raise ValueError('Missing movement hook')
  c=current[0]
  for name,key in (('x','px'),('y','py'),('z','pz')):
   if state[name]&0xffff!=c[key]:raise ValueError('Position mismatch')
  for name,key in (('vx','dx'),('vy','dy'),('vz','dz')):
   if state[name]!=c[key]|c[key+'_ext']<<16:raise ValueError('Velocity mismatch')
  if frame==target:break
  for pos,vel in (('x','vx'),('y','vy'),('z','vz')):state[pos]=(state[pos]+state[vel])&0xffffff
  state['vz']=(state['vz']+32)&0xffffff
  steps.append(frame)
 first=cap['samples'][1]
 if any((state[k]&0xffff if k in ('x','y','z') else state[k])!=first['before'][k] for k in state):raise ValueError('Visual excerpt does not join')
 results.append({'input':cap['input'],'graphics_sha256':cap['graphics_sha256'],'hooks_sha256':cap['hooks_sha256'],
  'launch_frame':shot['frame'],'input_word':final['input_word'],'flags':shot['flags'],'variant':shot['variant'],
  'index':shot['index'],'table_offset':offset,'vector':vector,'initial':initial,'free_steps':len(steps),'target_draw_frame':target})
if [r['free_steps'] for r in results]!=[10,11]:raise ValueError('Unexpected flight span')
output={'schema':'issd-penalty-launch-replay/v1','gravity':32,'captures':results,
 'limits':['Two synthetic recordings, direction sent to both controls.',
           'Only low position words were recorded; high position bytes are not recovered.',
           'Frames before the visual excerpt have movement hooks but no matching image in this dataset.',
           'Browser input mapping, collision selection and universal timing remain unproven.',
           'ROM, raw traces and images stay local.']}
Path('docs/issd-penalty-launch-replay.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-launch-replay.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 2 ROM vectors link launch to the captured motion excerpts')
