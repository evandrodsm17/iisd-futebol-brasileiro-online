"""Audit high-ball responses across speeds and preserve failed left-side coverage."""
import argparse,hashlib,json
from pathlib import Path

def read(path):return [json.loads(s) for s in path.read_bytes().splitlines()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def signed_v(r):
 v=(r['vx']<<16)|r['vxLo'];return v-(1<<32) if v&0x80000000 else v

def audit(right,left):
 all_results=[]
 for side,path in [(1,right),(-1,left)]:
  rows=read(path);cases={r['trial']:r for r in rows if r['type']=='case'}
  if len(cases)!=9 or any(sum(r['type']=='frame' and r['trial']==i for r in rows)!=40 for i in range(1,10)):raise ValueError('Incomplete test matrix')
  for i,c in sorted(cases.items()):
   if c['side']!=side or c['offset']!=0:raise ValueError('Unexpected case')
   hooks=[r for r in rows if r['type']=='hook' and r['trial']==i];frames=[r for r in rows if r['type']=='frame' and r['trial']==i]
   response=[r for r in hooks if r['pc']=='838B75'];score=[frames[-1]['score1'],frames[-1]['score2']]
   item={'side':side,'trial':i,'initial_height':c['height'],'initial_speed':c['speed'],'first_frame_native_x':frames[0]['nativeX'],'response':None,'score_after_40':score}
   if side==1 and c['height'] in (-63,-64):
    if len(response)!=1:raise ValueError('Missing high-ball response')
    step=response[0]['step'];entry=next(r for r in hooks if r['pc']=='838C51' and r['step']==step);exit=next(r for r in hooks if r['pc']=='83A900' and r['step']==step)
    before,after=signed_v(entry),signed_v(exit);sound=[r for r in hooks if r['pc']=='80BF05' and r['step']==step and (r['regA']&255)==44]
    expected=-65536 if c['speed']==2 else -(before//2)
    if after!=expected or len(sound)!=1 or score!=[0,0]:raise ValueError('Unexpected native response')
    item['response']={'step':step,'height_word':response[0]['z'],'native_x':response[0]['local2a'],'native_y':response[0]['local2c'],'vx_before_16_16':before,'vx_after_16_16':after,'audio_queue_byte':44}
   if side==1 and c['height']==-56 and score!=[1,0]:raise ValueError('Unexpected scoring outcome')
   if side==-1 and (response or frames[0]['nativeX']<32):raise ValueError('Left setup behaved differently; re-evaluate')
   all_results.append(item)
 return {'schema':'issd-high-ball-speed-study/v1','right_trace_sha256':sha(right),'left_trace_sha256':sha(left),'cases':all_results,'limits':['Synthetic states from separately prepared camera saves; no PCM recorded.','The right-hand samples test three initial speeds and two high starting heights only.','The left preparation did not preserve the intended initial position; no conclusion about left-side physics follows.','Observed native speeds and height thresholds are not yet mapped to browser units.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('right',type=Path);p.add_argument('left',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.right,a.left);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 9 right-side and 9 left-side trials; six right high-ball responses verified, left setup inconclusive')
if __name__=='__main__':main()
