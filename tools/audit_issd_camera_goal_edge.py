"""Validate camera target selection and a framed goal-edge replay."""
import argparse,collections,hashlib,json
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def signed_v(r):
 v=(r['vx']<<16)|r['vxLo'];return v-(1<<32) if v&0x80000000 else v

def audit(target,edge,image_before,image_after):
 rows=[json.loads(s) for s in target.read_bytes().splitlines()]
 selections={p:[r for r in rows if r['type']=='target' and r['phase']==p] for p in (1,2)}
 frames={p:[r for r in rows if r['type']=='frame' and r['phase']==p] for p in (1,2)}
 if len(selections[1])!=60 or len(selections[2])!=60 or any(len(frames[p])!=60 for p in (1,2)):raise ValueError('Incomplete camera selection')
 if any(r['x']!=0x500 or r['a6']!=0x500 for r in selections[1]):raise ValueError('Unexpected possessed target')
 if any(r['x']!=0x400 or r['a6']!=0 for r in selections[2]):raise ValueError('Unexpected free-ball target')
 replay=[json.loads(s) for s in edge.read_bytes().splitlines()]
 cases=[r for r in replay if r['type']=='case'];samples=[r for r in replay if r['type']=='frame'];hooks=[r for r in replay if r['type']=='hook']
 if len(cases)!=1 or len(samples)!=40:raise ValueError('Incomplete framed edge replay')
 wanted=['838BAB','838BC8','838BF8','838C3B','838C51','8390B3','83A900','838726','839073','8390CB','83A90E']
 if [r['pc'] for r in hooks]!=wanted or any(r['step']!=5 for r in hooks):raise ValueError('Unexpected hook path')
 before=next(r for r in hooks if r['pc']=='8390B3');after=next(r for r in hooks if r['pc']=='83A900')
 x,y=signed_v(before),signed_v(after)
 if x<=0 or y!=-(x//2):raise ValueError('Unexpected native velocity response')
 if before['x']>=256 or before['y']>=256:raise ValueError('Observed ball coordinates out of view')
 return {'schema':'issd-camera-and-goal-edge/v1','target_trace_sha256':digest(target),'edge_trace_sha256':digest(edge),'screenshot_before_sha256':digest(image_before),'screenshot_after_sha256':digest(image_after),'camera_selection':{'possessed':{'samples':60,'actor':1280,'carrier':1280},'free_ball':{'samples':60,'actor':1024,'carrier':0},'disassembly':'8B:81BA..825A'},'edge':{'cases':1,'warmup_frames':2100,'frames':40,'hook_step':5,'path':wanted,'ball_xy_before':[before['x'],before['y']],'native_xy':[before['local2a'],before['local2c']],'velocity_before_signed_16_16':x,'velocity_after_signed_16_16':y,'direction_before':before['direction'],'direction_after':after['direction'],'sound_queue_calls':sum(r['pc']=='80BF05' for r in hooks)},'limits':['Synthetic input and one saved state; selection policy includes other branches not covered.','Coordinates and screenshots show the scene, not a validated pixel-perfect collision point.','Audio queue calls alone do not capture PCM; no post sound is identified by this replay.','Only the entry of the subroutines is observed, and later helpers modify the velocity further.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('target',type=Path);p.add_argument('edge',type=Path);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.target,a.edge,a.before,a.after);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 120 camera selections, visible scene and one native edge velocity reversal')
if __name__=='__main__':main()
