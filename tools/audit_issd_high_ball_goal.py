"""Compare centered goal outcomes and native response at high ball positions."""
import argparse,hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sx(r):
 v=(r['vx']<<16)|r['vxLo'];return v-(1<<32) if v&0x80000000 else v

def audit(path,before,after):
 rows=[json.loads(s) for s in path.read_bytes().splitlines()]
 cases={r['trial']:r for r in rows if r['type']=='case'}
 if len(cases)!=25 or any(sum(r['type']=='frame' and r['trial']==i for r in rows)!=40 for i in range(1,26)):raise ValueError('Incomplete camera matrix')
 results=[]
 for trial in range(11,16):
  case=cases[trial];hooks=[r for r in rows if r.get('trial')==trial and r['type']=='hook'];frames=[r for r in rows if r.get('trial')==trial and r['type']=='frame']
  if case['offset']!=0 or case['side']!=1:raise ValueError('Unexpected test case')
  goal=[r for r in hooks if r['pc']=='86D98C'];impact=[r for r in hooks if r['pc']=='838B75'];audio=[r for r in hooks if r['pc']=='80BF05' and (r['regA']&255)==0x2c]
  result={'trial':trial,'initial_height':case['height'],'score_after_40':[frames[-1]['score1'],frames[-1]['score2']],'goal_hook_count':len(goal),'response_hook_count':len(impact),'sound_code_2c_count':len(audio)}
  if trial in (14,15):
   if len(impact)!=1 or len(audio)!=1 or impact[0]['step']!=audio[0]['step'] or goal:raise ValueError('Unexpected high-ball response')
   ix=next(r for r in hooks if r['pc']=='8390B3' and r['step']==impact[0]['step']);ox=next(r for r in hooks if r['pc']=='83A900' and r['step']==impact[0]['step']);vin,vout=sx(ix),sx(ox)
   if vin<=0 or vout!=-(vin//2):raise ValueError('Velocity reflection mismatch')
   result['response']={'frame':impact[0]['step'],'native_x':impact[0]['local2a'],'native_y':impact[0]['local2c'],'height_signed':impact[0]['z']-65536 if impact[0]['z']>=32768 else impact[0]['z'],'velocity_before_16_16':vin,'velocity_after_16_16':vout,'sound_code':44}
  elif len(goal)!=1 or impact or frames[-1]['score1']!=1:raise ValueError('Unexpected scoring outcome')
  results.append(result)
 return {'schema':'issd-high-ball-goal-matrix/v1','trace_sha256':sha(path),'before_screenshot_sha256':sha(before),'after_screenshot_sha256':sha(after),'cases_total':len(cases),'frames_per_case':40,'centered_cases':results,'limits':['Synthetic RAM states from a single right-side camera setup; not natural shots.','Code 2C is queued to the APU but no PCM was recorded or sound identified by ear for each case.','Screenshots establish visible scene only, not pixel-exact contact or whether the sound is the one the user heard.','The camera, field-unit conversion, other directions, velocities, and left-side behavior remain to be verified.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.trace,a.before,a.after);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 25 cases; 3 centered goals and 2 high-ball responses with sound code 2C')
if __name__=='__main__':main()
