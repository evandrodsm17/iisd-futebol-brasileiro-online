"""Summarize an automated probe without inferring causality or gameplay actions."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def analyze(rows):
    start=end=None; samples=0; valid=Counter(); held=Counter(); settings=Counter(); last=0
    for row in rows:
        if row.get('type')=='session_start':
            if start is not None: raise ValueError('Duplicate session start')
            start=row;continue
        if row.get('type')=='session_end': end=row;continue
        if row.get('type'): continue
        step=row['step']
        if step<=last: raise ValueError('Non-monotonic step')
        last=step;samples+=1
        name=row['input'];held[(name,row['held_p1'])]+=1
        if row.get('actor_slot_valid'):
            valid[name]+=1;settings[row['player_setting']]+=1
    return {'samples':samples,'last_step':last,'complete':bool(end and start and end['steps']==start['target_frames']),
            'valid_actor_samples_by_input':dict(valid),
            'player_settings_when_actor_valid':dict(settings),
            'held_words_by_input':[{'input':a,'held':b,'samples':n} for (a,b),n in held.most_common()],
            'limitations':['Input labels are injected commands; held word confirms game-side observation only.',
                           'A valid actor slot and player setting do not alone prove a controlled movement.',
                           'Two-frame sampling and stoppages prevent speed calibration.',
                           'Screenshot observations require separate visual review.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=hashlib.sha256()
    def rows():
        with a.trace.open('rb') as f:
            for line in f:
                digest.update(line)
                if line.strip(): yield json.loads(line)
    result=analyze(rows());result['schema']='issd-auto-probe-summary/v1'
    result['source']={'path':a.trace.as_posix(),'bytes':a.trace.stat().st_size,'sha256':digest.hexdigest()}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('complete:',result['complete'],'samples:',result['samples'],'valid actors:',result['valid_actor_samples_by_input'])
