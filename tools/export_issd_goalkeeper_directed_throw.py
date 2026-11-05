"""Validate two additional captured goalkeeper high-throw orientations."""
import argparse,hashlib,json,tempfile
from pathlib import Path
from PIL import Image
from verify_issd_goalkeeper_throw_frame import export as verify

CASES={
 '7':{'name':'Up','durations':[2,2,2,2,20],'frames':[(70,4517,4519,0xc877),(69,4518,4519,0xc87c),(70,4521,4522,0xc881),(70,4524,4525,0xc886),(70,4527,4528,0xc88b)]},
 '1':{'name':'Down','durations':[2,2,2,3,22],'frames':[(70,4517,4519,0xc8bd),(69,4518,4519,0xc8c2),(70,4521,4522,0xc8c7),(70,4523,4525,0xc8cc),(70,4527,4528,0xc8d1)]}}

def build(analysis,rom,state,output_dir):
 results={}
 for direction,case in CASES.items():
  name=case['name'];sheet=Image.new('RGBA',(480,96),(0,0,0,0));reports=[]
  timeline=analysis/'keeper-directed-graphics'/name/'B'/'trial.jsonl'
  rows=[json.loads(x) for x in timeline.read_text(encoding='utf8').splitlines() if '"step"' in x]
  actual=[x for x in rows if x['script'] in (0xe625,0xe644)]
  expected=[desc for (_,_,_,desc),count in zip(case['frames'],case['durations']) for _ in range(count)]
  if [x['descriptor'] for x in actual]!=expected or any(x['direction']!=int(direction) for x in actual):raise ValueError('Timeline mismatch')
  with tempfile.TemporaryDirectory() as tmp:
   for i,(start,prepared,displayed,desc) in enumerate(case['frames']):
    root=analysis/'keeper-directed-graphics'/name/'B' if start==70 else analysis/'keeper-directed-offset'/name/str(start)
    neutral=analysis/'keeper-directed-graphics'/name/'NEUTRAL' if start==70 else analysis/'keeper-directed-neutral69'/name
    image=Path(tmp)/f'{i}.png';r=verify(root,neutral,rom,image,prepared,displayed,state,True)
    if r['descriptor']!=desc or r['direction']!=int(direction):raise ValueError('Wrong pose')
    with Image.open(image) as im:sheet.paste(im,(96*i,0))
    reports.append(r)
  output_dir.mkdir(parents=True,exist_ok=True);path=output_dir/f'goalkeeper-throw-{direction}.png';sheet.save(path)
  results[direction]={'duration_frames':case['durations'],'timeline_start':actual[0]['frame'],'timeline_end':actual[-1]['frame'],
     'timeline_sha256':hashlib.sha256(timeline.read_bytes()).hexdigest(),'sheet_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':reports}
 return {'schema':'issd-goalkeeper-directed-throw-audit/v1','state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),'directions':results,
  'limitations':['One goalkeeper and one palette; screen orientation mapping is not validated.',
   'One reference pose per direction comes from a different B timing; timelines come from their own 70-step trials.',
   'Some screenshot mismatches match earlier OAM pixels; occluder identity is unconfirmed.',
   'Final hold is only the observed interval; subsequent movement and ball physics remain unvalidated.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
 a=p.parse_args();r=build(a.analysis,a.rom,a.state,a.output_dir);a.evidence.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: 10 poses across two directions')
if __name__=='__main__':main()
