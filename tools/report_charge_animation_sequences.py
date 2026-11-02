"""Report uninterrupted sampled actor runs; do not infer missing poses or durations."""
import argparse
import hashlib
import json
from pathlib import Path

TARGET={0x438,0x468}


def analyze(lines):
    active={};runs=[];last_frame=None
    def close(address):
        runs.append(active.pop(address))
    for line in lines:
        if not line.strip(): continue
        row=json.loads(line);frame=row['frame']
        if not isinstance(frame,int) or (last_frame is not None and frame<=last_frame):
            raise ValueError('Non-monotonic frames')
        actors={a['address']:a for a in row.get('actors',[]) if isinstance(a.get('address'),int)}
        for address in list(active):
            a=actors.get(address)
            if frame-last_frame!=2 or not a or a.get('state') not in TARGET or a.get('animation_script')!=0xcf9f:
                close(address)
        for address,a in actors.items():
            if a.get('state') not in TARGET or a.get('animation_script')!=0xcf9f: continue
            if address not in active:
                active[address]={'actor':address,'samples':[]}
            active[address]['samples'].append({k:a.get(k) for k in
                ('state','direction','descriptor','animation_cursor','animation_timer','animation_duration') } | {'frame':frame})
        last_frame=frame
    for address in list(active): close(address)
    return runs


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    digest=hashlib.sha256()
    def lines():
        with args.trace.open('rb') as f:
            for line in f:
                digest.update(line);yield line
    runs=analyze(lines())
    result={'schema':'issd-charge-animation-runs/v1','source':{'path':args.trace.as_posix(),
      'sha256':digest.hexdigest(),'bytes':args.trace.stat().st_size},'runs':runs,
      'limitations':['Sampling occurs every two frames; missing intermediate poses are unknown.',
                     'Capture filters actors; run boundaries may be incomplete.',
                     'No OAM/VRAM pairing or action labels are proven.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'{len(runs)} observed runs; {sum(len(r["samples"]) for r in runs)} samples')
