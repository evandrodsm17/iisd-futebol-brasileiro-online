"""Audit a controlled hold-duration replay from a single pre-shot state."""
import argparse,hashlib,json
from pathlib import Path

def fixed(row,name):
 n=(row[name]<<16)|row[name+'Frac'];return (n-(1<<32) if n&0x80000000 else n)/65536

def audit(path,state):
 data=path.read_bytes();rows=[json.loads(s) for s in data.splitlines()];cases={r['trial']:r for r in rows if r['type']=='case'}
 if len(cases)!=6:raise ValueError('Incomplete duration matrix')
 expected=[(1,0,-.25),(3,2,-.5),(6,5,-1.5),(10,9,-2.25),(15,11,-2.5),(20,11,-2.5)];out=[]
 for i,(held,count,vz) in enumerate(expected,1):
  c=cases[i];h=[r for r in rows if r.get('trial')==i and r['type']=='hook'];f=[r for r in rows if r.get('trial')==i and r['type']=='frame']
  if len(f)!=45 or c['heldFrames']!=held:raise ValueError('Incomplete trial')
  releases=[r for r in h if r['site']=='85F89B']
  if len(releases)!=1:raise ValueError('Unexpected release count')
  release=releases[0];sample=next(r for r in f if r['step']==release['step'])
  if release['x']!=5 or release['y']!=count or release['charge']!=count or sample['ballType']!=5 or sample['carrier']!=0 or fixed(sample,'vz')!=vz:raise ValueError('Unexpected release behavior')
  if i==6 and not release['held']&0x40:raise ValueError('Long hold was not active at release')
  if i<6 and release['held']&0x40:raise ValueError('Button still held at release')
  charge=[r for r in h if r['site']=='80DA68']
  if not any(r['charge']==count for r in charge):raise ValueError('Charge not observed')
  out.append({'held_frames':held,'release_step':release['step'],'native_charge':count,'button_still_held_at_release':bool(release['held']&0x40),'ball_type':sample['ballType'],'velocity_x':fixed(sample,'vx'),'velocity_y':fixed(sample,'vy'),'velocity_z':fixed(sample,'vz')})
 return {'schema':'issd-shot-hold-duration/v1','trace_sha256':hashlib.sha256(data).hexdigest(),'seed_state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),'trials':out,'limitations':['One isolated pre-shot saved state, actor, facing, weather and ball type; not a universal control rule.','Held-frame count is input injected to BizHawk; native charge starts after input handling and may differ.','Velocity is sampled at frame end after release, not at the exact instruction that initializes it.','Only six durations were observed; no interpolation or native-to-web scale is implied.','The seed savestate and ROM remain local.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('state',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.trace,a.state);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: six hold durations, charge 0..11 and observed release velocities')
if __name__=='__main__':main()
