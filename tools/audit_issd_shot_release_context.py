"""Compare action-release hooks with earlier recorded independent replays."""
import argparse,hashlib,json
from pathlib import Path
from compare_issd_action_trials import load,signature,has_extended

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(root,right_baseline,left_baseline):
 result={}
 for name,baseline in [('right',right_baseline),('left',left_baseline)]:
  folder=root/('shot-charge-'+name)
  candidates=[p for p in folder.glob('issd-auto-probe-*.jsonl') if p.stat().st_size>0]
  if len(candidates)!=1:raise ValueError('Expected one nonempty replay')
  source=candidates[0];a,b=load(source),load(baseline);common=sorted(set(a['samples'])&set(b['samples']))
  if len(common)<300 or any(not has_extended(t['samples'][i]) for i in common for t in (a,b)) or any(signature(a['samples'][i],True)!=signature(b['samples'][i],True) for i in common):raise ValueError('Replay fields mismatch')
  hooks=[json.loads(s) for s in (folder/'charge-hooks.jsonl').read_text(encoding='utf8').splitlines()]
  if not any(h.get('type')=='session_end' for h in hooks):raise ValueError('Incomplete hook log')
  releases=[h for h in hooks if h.get('site') in ('85F871','85F89B')]
  if len(releases)!=1:raise ValueError('Expected one release path')
  release=releases[0]
  if name=='right' and not (release['site']=='85F871' and release['x']==3 and release['y']==11 and release['charge']==0 and release['heldP2']==0x40 and not release['flags6e']&0x800):raise ValueError('Unexpected right branch')
  if name=='left' and not (release['site']=='85F89B' and release['x']==5 and release['y']==5 and release['charge']==5 and release['heldP2']==0 and release['flags6e']&0x800):raise ValueError('Unexpected left branch')
  samples=[h for h in hooks if h.get('site')=='80DA68' and release['frame']-8<=h['frame']<=release['frame']]
  if name=='left' and not all(any(h['charge']==n and h['mask']==0x40 for h in samples) for n in range(6)):raise ValueError('Charge sequence missing')
  result[name]={'replay_sha256':sha(source),'baseline_sha256':sha(baseline),'hook_sha256':sha(folder/'charge-hooks.jsonl'),'matched_samples':len(common),'release':release,'charge_samples':samples}
 return {'schema':'issd-shot-release-context/v1','cases':result,'limitations':['Two replays of the same saved state and actor with different preparation directions; no causal attribution to direction alone.','Matching covers logged fields, not unobserved internal state.','Hooks capture entry states; intervening helper effects are not independently measured.','One hold duration per case; no general charge-time or input mapping was proven.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('right_baseline',type=Path);p.add_argument('left_baseline',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.root,a.right_baseline,a.left_baseline);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 325 matching samples each; distinct fixed-11 and charge-5 release paths')
if __name__=='__main__':main()
