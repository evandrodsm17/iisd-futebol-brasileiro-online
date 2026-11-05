"""Validate five ROM goalkeeper throw poses and build a local lab sheet."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from PIL import Image
from verify_issd_goalkeeper_throw_frame import export as verify

# Sources are independent natural replays from the same saved state; each pair
# names an observed draw-prepared frame and its compared displayed frame.
CASES=[('23',4470,4471,0xc89a),('20',4470,4471,0xc89f),
       ('20',4472,4474,0xc8a4),('21',4476,4477,0xc8a9),('20',4476,4477,0xc8ae)]
DURATIONS=[1,2,2,3,20]

def build(analysis,rom,state,output):
    neutral=analysis/'keeper-action-trials'/'NEUTRAL';reports=[];sheet=Image.new('RGBA',(96*len(CASES),96),(0,0,0,0))
    source_trace=analysis/'keeper-action-timing'/'20-B'/'trial.jsonl'
    samples=[json.loads(x) for x in source_trace.read_text(encoding='utf8').splitlines() if '"step"' in x]
    target=[r for r in samples if 4468<=r['frame']<4496]
    wanted=[d for (_,_,_,d),n in zip(CASES,DURATIONS) for _ in range(n)]
    if len(target)!=len(wanted) or [r['descriptor'] for r in target]!=wanted:
        raise ValueError('Original timing replay differs from observed timeline')
    with tempfile.TemporaryDirectory() as tmp:
        for i,(case,prep,display,desc) in enumerate(CASES):
            root=(analysis/'keeper-throw-window'/'B') if case=='20' else (analysis/'keeper-throw-offset'/case)
            image=Path(tmp)/f'{i}.png'
            result=verify(root,neutral,rom,image,prep,display,state)
            if result['descriptor']!=desc:raise ValueError('Pose mismatch')
            with Image.open(image) as frame:sheet.paste(frame,(96*i,0))
            reports.append(result)
    output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output)
    return {'schema':'issd-goalkeeper-throw-sequence-audit/v1','rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
       'state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(), 'timeline_trace_sha256':hashlib.sha256(source_trace.read_bytes()).hexdigest(),
       'timeline_start':4468,'timeline_end_exclusive':4496,'durations_frames':DURATIONS,'frames':reports,
       'sheet_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
       'limitations':['One goalkeeper, one direction, palette and initial state.',
         'Pose references use distinct B trials; timing comes from one complete B trial.',
         'Some screenshot differences coincide with earlier OAM pixels; object identity and visual priority remain unproven.',
         'The last 20 frames are the observed hold, not proof of the full follow-through.',
         'Possession, ball release physics, other directions and team variants remain unverified.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'))
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True)
    p.add_argument('--sheet',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();r=build(a.analysis,a.rom,a.state,a.sheet);a.evidence.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    print('OK: five poses, 28 observed frames')
if __name__=='__main__':main()
