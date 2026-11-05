"""Compare isolated goalkeeper button trials against the same neutral state."""
import argparse
import hashlib
import json
from pathlib import Path

MASKS={'A':0x80,'B':0x8000,'X':0x40,'Y':0x4000}
IGNORE={'input','held_p1'}

def read(path):
    rows=[json.loads(x) for x in path.read_text(encoding='utf8').splitlines()]
    starts=[x for x in rows if x.get('type')=='session_start'];ends=[x for x in rows if x.get('type')=='session_end']
    samples={x['step']:x for x in rows if 'step' in x}
    if len(starts)!=1 or len(ends)!=1 or set(samples)!=set(range(1,181)):raise ValueError('Incomplete trial')
    return starts[0],samples

def audit(neutral, trials, state):
    base_header,base=read(neutral)
    if base_header['button']!='NEUTRAL' or any(x['held_p1'] for x in base.values()):raise ValueError('Control is not neutral')
    results=[]
    for path in trials:
        header,case=read(path);button=header['button'];start=header['start'];duration=header['duration']
        if button not in MASKS or duration!=6:raise ValueError('Unexpected trial')
        if header['state_frame']!=base_header['state_frame']:raise ValueError('Different initial frame')
        fields=set(base[1])-IGNORE
        def changes(t):return [key for key in fields if case[t][key]!=base[t][key]]
        if any(changes(t) for t in range(1,start)):raise ValueError('State differs before input')
        for t in range(1,181):
            expected=MASKS[button] if start<=t<start+duration else 0
            if case[t]['held_p1']!=expected or base[t]['held_p1']!=0:raise ValueError('Input not delivered')
        if any(case[t]['selected']!=0x500 for t in range(start,start+duration)):raise ValueError('Goalkeeper not selected')
        differing=[t for t in range(start,181) if changes(t)]
        transitions=[];previous=None
        for t,row in case.items():
            key=(row['state'],row['script'],row['descriptor'])
            if key!=previous:
                transitions.append({'step':t,'frame':row['frame'],'state':key[0],'script':key[1],
                  'descriptor':key[2],'pose':row['pose'],'direction':row['direction']})
                previous=key
        results.append({'button':button,'start':start,'duration':duration,'trial_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'pre_input_samples_match':start-1,'selected_goalkeeper_and_input_confirmed':True,
          'first_observed_difference':differing[0] if differing else None,'differing_samples':len(differing),
          'transitions':transitions})
    return {'schema':'issd-goalkeeper-input-audit/v1','state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
      'neutral_sha256':hashlib.sha256(neutral.read_bytes()).hexdigest(),'trials':results,
      'limitations':['Same saved state and recorded fields do not prove all hidden state is identical.',
        'Differences correlate with these specific inputs and scenario; do not establish general mechanics.',
        'Raw ball coordinates and carrier field do not alone establish possession, release timing or shot physics.',
        'Visual sequences need independent OAM/VRAM/CGRAM/screenshot validation.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--neutral',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True);p.add_argument('--trials',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.neutral,a.trials,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print(f"OK: {len(r['trials'])} paired input trials")
if __name__=='__main__':main()
