"""Inventory charge-route actor states and CF9F descriptors in existing traces."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

STATES={0x430,0x438,0x440,0x460,0x468,0x470}


def analyze(lines):
    frames=0; states=Counter(); scripts=Counter(); descriptors=Counter(); directions=Counter()
    transitions=Counter(); previous={}; last_frame=None
    for line in lines:
        if not line.strip(): continue
        row=json.loads(line); frame=row['frame']
        if not isinstance(frame,int) or (last_frame is not None and frame<=last_frame):
            raise ValueError('Missing or non-monotonic frame')
        current={}
        for actor in row.get('actors',[]):
            address=actor.get('address');state=actor.get('state');script=actor.get('animation_script')
            if not isinstance(address,int) or not isinstance(state,int): continue
            current[address]=state
            # Captures sample every other frame; only count transitions where
            # no intermediate sampled record is missing, never claim exact timing.
            if last_frame is not None and frame-last_frame==2 and address in previous:
                old=previous[address]
                if old!=state and (old in STATES or state in STATES): transitions[(old,state)]+=1
            if state not in STATES: continue
            states[state]+=1
            if isinstance(script,int): scripts[(state,script)]+=1
            if script==0xcf9f:
                descriptor=actor.get('descriptor');direction=actor.get('direction')
                if isinstance(descriptor,int): descriptors[descriptor]+=1
                if isinstance(direction,int): directions[direction]+=1
        previous=current;last_frame=frame;frames+=1
    return {'frames':frames,'state_samples':{f'{k:04X}':v for k,v in sorted(states.items())},
            'state_script_samples':[{'state':f'{a:04X}','script':f'{b:04X}','samples':v}
                                    for (a,b),v in scripts.most_common()],
            'cf9f_descriptors_in_target_states':{f'{k:04X}':v for k,v in sorted(descriptors.items())},
            'cf9f_directions_in_target_states':dict(sorted(directions.items())),
            'sampled_state_transitions':[{'from':f'{a:04X}','to':f'{b:04X}','count':v}
                                         for (a,b),v in transitions.most_common()]}


def analyze_path(path):
    digest=hashlib.sha256()
    def lines():
        with path.open('rb') as stream:
            for line in stream:
                digest.update(line)
                yield line
    result=analyze(lines())
    result['source']={'path':path.as_posix(),'sha256':digest.hexdigest(),'bytes':path.stat().st_size}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('traces',type=Path,nargs='+')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result={'schema':'issd-charge-animation-trace/v1','traces':[analyze_path(p) for p in args.traces],
            'limitations':['Two-frame sampling cannot prove exact transition timing.',
                           'Actor capture filters omit some objects and frames.',
                           'Descriptors and state do not identify an action without visual input evidence.',
                           'OAM pixels, palettes and full pose sequence are not validated by this report.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for trace in result['traces']: print(trace['source']['path'],trace['frames'],trace['state_samples'])
