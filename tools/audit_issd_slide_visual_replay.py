"""Correlate a passive slide replay's timeline with same-frame graphics captures."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import load, signature, has_extended


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root, neutral_path, asset_map, state):
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1: raise ValueError('Expected one replay trace')
    a,n=load(paths[0]),load(neutral_path)
    common=sorted(set(a['samples'])&set(n['samples']))
    before=[t for t in common if 0<=t<480]
    if not (any(set(range(i,480,2))<=set(before) for i in (0,1)) and
            all(has_extended(rows[t]) for rows in (a['samples'],n['samples']) for t in before) and
            all(signature(a['samples'][t],True)==signature(n['samples'][t],True) for t in before) and
            all(a['samples'][t]['held_p1']==0x80 and n['samples'][t]['held_p1']==0 for t in range(480,486))):
        raise ValueError('Baseline or input mismatch')
    actor=a['samples'][479]['selected_p1']
    timeline=[]
    for t in range(480,511):
        r=a['samples'][t]; v=r['actor']
        if r['selected_p1']!=actor: raise ValueError('Selected actor changed during timeline')
        item={'elapsed':t,'frame':r['frame'],'state':v['state'],'script':v['script'],
              'descriptor':v['descriptor'],'direction':v['direction']}
        if timeline and all(timeline[-1][k]==item[k] for k in ('state','script','descriptor','direction')):
            timeline[-1]['last_elapsed']=t;timeline[-1]['last_frame']=r['frame'];timeline[-1]['samples']+=1
        else:
            item.update(last_elapsed=t,last_frame=r['frame'],samples=1);timeline.append(item)
    mapping={}
    for family in json.loads(asset_map.read_text(encoding='utf-8'))['scripts']:
        for f in family['frames']: mapping[(family['script'],f['descriptor'])]=f
    snapshots=[]
    for line in (root/'slide-poses.jsonl').read_text().splitlines():
        s=json.loads(line)
        matching=[r for r in a['samples'].values() if r['frame']==s['frame'] and r['selected_p1']==s['actor']]
        if len(matching)!=1 or any(matching[0]['actor'][field]!=s[field] for field in ('state','script','descriptor','direction')):
            raise ValueError('Snapshot does not match frame-end actor sample')
        stem=s.pop('stem'); files={}
        for suffix,size in [('mirror.bin',544),('vram.bin',65536),('cgram.bin',512),('ppu.bin',544)]:
            path=root/(stem+'-'+suffix)
            if not path.is_file() or path.stat().st_size!=size: raise ValueError(f'Missing graphics: {path}')
            files[suffix]=sha(path)
        f=mapping.get((f'${s["script"]:04X}',f'${s["descriptor"]:04X}'))
        snapshots.append({**s,'local_files_sha256':files,'asset_map':f})
    if len(snapshots)!=6 or not all(s['ppu_available'] for s in snapshots): raise ValueError('Expected six PPU captures')
    return {'schema':'issd-slide-visual-replay/v1','declared_state_sha256':sha(state),
            'trace_sha256':a['sha256'],'neutral_trace_sha256':n['sha256'],
            'baseline_samples':len(before),'actor':actor,'timeline':timeline,'snapshots':snapshots,
            'limitations':['OAM includes all visible objects; actor slot assignment is not validated.',
                           'Same-frame records do not prove PPU and WRAM belong to the same animation phase.',
                           'Timing describes one observed direction and scenario, not all slide animations.',
                           'Graphics files and screenshots are local only; no spritesheet is validated here.',
                           'The declared state is not authenticated by the emulator trace.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--neutral',required=True,type=Path);p.add_argument('--asset-map',required=True,type=Path);p.add_argument('--state',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();args.output.write_text(json.dumps(audit(args.root,args.neutral,args.asset_map,args.state),indent=2)+'\n',encoding='utf-8');print('audited slide animation replay')
