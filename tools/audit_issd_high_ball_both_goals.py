"""Compare centered high-ball outcomes on both ends using two ROM replays."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signed(r):
 n=(r['vx']<<16)|r['vxLo'];return n-(1<<32) if n&0x80000000 else n

def audit(right,left,screen):
 results=[]
 for side,path in [(1,right),(-1,left)]:
  rows=[json.loads(s) for s in path.read_bytes().splitlines()];cases={r['trial']:r for r in rows if r['type']=='case'}
  if len(cases)!=9 or any(sum(r['type']=='frame' and r['trial']==i for r in rows)!=40 for i in range(1,10)):raise ValueError('Incomplete capture')
  for i,c in sorted(cases.items()):
   h=[r for r in rows if r['type']=='hook' and r['trial']==i];f=[r for r in rows if r['type']=='frame' and r['trial']==i]
   if c['side']!=side or c['offset']!=0:raise ValueError('Unexpected case')
   goal=[r for r in h if r['pc']=='86D98C'];impact=[r for r in h if r['pc']=='838B75'];score=[f[-1]['score1'],f[-1]['score2']]
   item={'side':side,'trial':i,'initial_height':c['height'],'initial_speed':c['speed'],'first_frame_native_x':f[0]['nativeX'],'score_after_40':score,'response':None}
   if c['height']==-56:
    if len(goal)!=1 or impact or score!=([1,0] if side==1 else [0,1]):raise ValueError('Expected goal not observed')
   else:
    if len(impact)!=1 or goal or score!=[0,0]:raise ValueError('Expected response not observed')
    step=impact[0]['step'];entry=next(r for r in h if r['pc']=='838C51' and r['step']==step);exit=next(r for r in h if r['pc']=='83A900' and r['step']==step)
    vin,vout=signed(entry),signed(exit);snd=[r for r in h if r['pc']=='80BF05' and r['step']==step and (r['regA']&255)==44]
    expected=-65536 if side==1 and c['speed']==2 else -(vin//2) if vin>0 else ((-vin)//2)
    if vout!=expected or len(snd)!=1:raise ValueError('Unexpected velocity or audio command')
    item['response']={'step':step,'native_x':impact[0]['local2a'],'native_y':impact[0]['local2c'],'velocity_before_16_16':vin,'velocity_after_16_16':vout,'audio_queue_byte':44}
   results.append(item)
 return {'schema':'issd-high-ball-both-goals/v1','right_trace_sha256':sha(right),'left_trace_sha256':sha(left),'left_screenshot_sha256':sha(screen),'cases':results,'limitations':['Synthetic memory injections; two separate saved camera states.','The audio queue byte is not a PCM recording and the exact sound has not been separately identified.','These three speeds and two high starting heights do not cover all original match conditions.','Native-to-browser unit mapping and precise post/crossbar geometry remain unverified.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('right',type=Path);p.add_argument('left',type=Path);p.add_argument('screen',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.right,a.left,a.screen);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 18 cases, 6 scoring shots and 12 high-ball responses across both goals')
if __name__=='__main__':main()
