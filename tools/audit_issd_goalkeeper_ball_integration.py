"""Audit goalkeeper-throw ball integration at entry and return, 16.16 words."""
import argparse,collections,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

CODE=bytes.fromhex('18b50675229506b508752495088dc81b18b50a7526950ab50c7528950c95128dcc1b60')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def fixed(hi,lo):return (hi<<16)|lo
def signed(n):return n-0x100000000 if n&0x80000000 else n

def audit(root,reference,rom_path,state):
 raw=rom_path.read_bytes();head=len(raw)%0x8000
 if head not in (0,512) or hashlib.md5(raw[head:]).hexdigest()!=EXPECTED_MD5 or raw[head+0x189fb:head+0x189fb+len(CODE)]!=CODE:raise ValueError('Unexpected ROM integration code')
 directions={}
 for name,idx in [('Side','0'),('Up','7'),('Down','1')]:
  a=root/name/'B';n=root/name/'NEUTRAL'
  for button,folder in (('B',a),('NEUTRAL',n)):
   if (folder/'trial.jsonl').read_bytes()!=(reference/name/button/'trial.jsonl').read_bytes():raise ValueError('Reference trial differs')
  rows=read(a/'keeper-transfers.jsonl');control=read(n/'keeper-transfers.jsonl')
  if not all(any(x.get('type')=='session_end' for x in rs) for rs in (rows,control)):raise ValueError('Incomplete capture')
  events=[x for x in rows if x.get('type')=='ball_integration'];pairs=[];pending=None
  for event in events:
   if event['address']=='8389FB':
    if pending:raise ValueError('Nested integration entry')
    pending=event
   elif event['address']=='838A1D':
    if not pending or pending['frame']!=event['frame']:raise ValueError('Unpaired integration return')
    if pending['ball_type']==10:
     if event['ball_type']!=10 or pending['xreg']!=0x400 or event['xreg']!=0x400:raise ValueError('Unexpected ball context')
     for axis in ('x','y'):
      predicted=(fixed(pending[axis],pending[axis+'_frac'])+fixed(pending['v'+axis],pending['v'+axis+'_frac']))&0xffffffff
      if predicted!=fixed(event[axis],event[axis+'_frac']):raise ValueError('Integration result mismatch')
     pairs.append((pending,event))
    pending=None
  if pending or not pairs:raise ValueError('Missing integration observations')
  between={'x':collections.Counter(),'y':collections.Counter()}
  for (before,after),(nxt,_) in zip(pairs,pairs[1:]):
   if nxt['frame']!=before['frame']+1:continue
   for axis in ('x','y'):
    delta=(fixed(nxt[axis],nxt[axis+'_frac'])-fixed(after[axis],after[axis+'_frac']))&0xffffffff
    between[axis][str(signed(delta))]+=1
  directions[idx]={'pair_count':len(pairs),'first_frame':pairs[0][0]['frame'],'last_frame':pairs[-1][0]['frame'],
    'first_entry':pairs[0][0],'first_return':pairs[0][1],
    'next_entry_minus_return_16_16':{k:dict(sorted(v.items())) for k,v in between.items()},
    'action_trace_sha256':digest(a/'keeper-transfers.jsonl'),'neutral_trace_sha256':digest(n/'keeper-transfers.jsonl'),
    'action_trial_sha256':digest(a/'trial.jsonl'),'neutral_trial_sha256':digest(n/'trial.jsonl')}
 return {'schema':'issd-goalkeeper-ball-integration-audit/v1','rom_sha256':hashlib.sha256(raw[head:]).hexdigest(),'state_sha256':digest(state),'routine':'$83:89FB..$83:8A1D','ball_type':10,'directions':directions,
  'limitations':['Entry-to-return proves only the observed X/Y integration routine and path, not full ball physics.',
   'Next-entry differences include all operations between callbacks and are not identified as drag, camera or collisions.',
   'One goalkeeper, one saved state and three directions; Z, field limits and subsequent collisions remain separate.',
   '16.16 native units are not calibrated browser-world distances or velocities.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path('analysis/keeper-ball-integration'));p.add_argument('--reference',type=Path,default=Path('analysis/keeper-vector-hooks'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.reference,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK:',sum(x['pair_count'] for x in r['directions'].values()),'paired integration calls')
if __name__=='__main__':main()
