"""Audit a goalkeeper observer replay against an uninstrumented control."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import load, signature, has_extended


def one_log(root):
    logs=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(logs)!=1:raise ValueError('Expected exactly one probe log')
    return load(logs[0])


def audit(observed,control,state):
    a=one_log(observed);b=one_log(control)
    common=sorted(a['samples'].keys() & b['samples'].keys())
    if not common or set(a['samples'])!=set(b['samples']):raise ValueError('Sample coverage differs')
    if not all(has_extended(a['samples'][t]) and has_extended(b['samples'][t]) for t in common):
        raise ValueError('Extended state missing')
    differences=[t for t in common if signature(a['samples'][t],True)!=signature(b['samples'][t],True)
        or any(a['samples'][t].get(k)!=b['samples'][t].get(k) for k in ('input','input_p2','held_p1','held_p2'))]
    if differences:raise ValueError(f'Observer/control diverged at {differences[0]}')
    path=observed/'keeper-transfers.jsonl';rows=[json.loads(s) for s in path.read_text(encoding='utf8').splitlines()]
    starts=[x for x in rows if x.get('type')=='session_start'];ends=[x for x in rows if x.get('type')=='session_end']
    if len(starts)!=1 or len(ends)!=1:raise ValueError('Incomplete observer log')
    calls=[r for r in rows if r.get('type')=='transfer_entry']
    frames=[r for r in rows if r.get('type')=='keeper_frame']
    if ends[0]['transfers']!=len(calls) or ends[0]['keeper_frames']!=len(frames):raise ValueError('Incomplete observer counts')
    if any(r['guards_allow']!=(r['guard_actor']==0 and r['guard_global']==0 and r['dma_used']<r['dma_limit']) for r in calls):
        raise ValueError('Incorrect guard evaluation')
    directions=Counter(str(r['script']) for r in frames if r['script'] in (0xE7C7,0xE7E3,0xE80A))
    return {'schema':'issd-keeper-transfer-audit/v1',
      'state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
      'observer_trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'observer_probe_sha256':a['sha256'],'control_probe_sha256':b['sha256'],
      'comparison':{'samples':len(common),'first_elapsed':common[0],'last_elapsed':common[-1],
                    'observed_field_mismatches':len(differences)},
      'observer':{'keeper_frames':len(frames),'transfers':len(calls),
        'actor_guard_nonzero':sum(r['guard_actor']!=0 for r in calls),
        'global_guard_nonzero':sum(r['guard_global']!=0 for r in calls),
        'capacity_guard_active':sum(r['dma_used']>=r['dma_limit'] for r in calls),
        'all_guards_allow':sum(r['guards_allow'] for r in calls),
        'target_script_samples':dict(directions)},
      'limitations':['Only recorded state and inputs are compared; hidden emulator state is not proven identical.',
        'Entry hooks show pre-instruction guards, not proof of the completed transfer.',
        'Frame-end samples are not synchronized PPU/OAM/VRAM/CGRAM evidence.',
        'A scenario without target script does not validate goalkeeper defenses or throws.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('observed',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.observed,a.control,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print(f"OK: {r['comparison']['samples']} matching state samples, {r['observer']['transfers']} keeper transfer entries")

if __name__=='__main__':main()
