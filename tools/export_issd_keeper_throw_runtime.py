"""Export observed goalkeeper-throw cycles for local descriptor rendering."""
import argparse,base64,hashlib,json,tempfile
from pathlib import Path
from export_issd_goalkeeper_throw_sequence import CASES,DURATIONS
from export_issd_goalkeeper_directed_throw import CASES as DIRECTED_CASES
from verify_issd_goalkeeper_throw_frame import export as verify
from render_issd_descriptor_sprite import descriptor_tiles
from audit_issd_slide_timing_geometry import rom_parts

def build(analysis,rom_path,state,output):
 raw=rom_path.read_bytes();header=len(raw)%0x8000
 if header not in (0,512):raise ValueError('Unexpected ROM header')
 rom=raw[header:];baseline=analysis/'keeper-action-trials'/'NEUTRAL';palette=None;cycles={};reports={}
 timing=analysis/'keeper-action-timing'/'20-B'/'trial.jsonl'
 samples=[json.loads(line) for line in timing.read_text(encoding='utf8').splitlines() if '"step"' in line]
 observed=[x['descriptor'] for x in samples if 4468<=x['frame']<4496]
 expected=[descriptor for (_,_,_,descriptor),duration in zip(CASES,DURATIONS) for _ in range(duration)]
 if observed!=expected:raise ValueError('Unexpected captured timing')
 with tempfile.TemporaryDirectory() as tmp:
  def add_frame(root,control,prepared,displayed,descriptor,direction,directed):
   nonlocal palette
   report=verify(root,control,rom_path,Path(tmp)/f'{direction}-{descriptor}.png',prepared,displayed,state,directed)
   if report['descriptor']!=descriptor or report['direction']!=int(direction):raise ValueError('Unexpected descriptor')
   events=[json.loads(line) for line in (root/'keeper-transfers.jsonl').read_text(encoding='utf8').splitlines()]
   graphics=[event for event in events if event.get('type')=='graphics' and event.get('actor')==0x500 and event.get('frame')==displayed]
   if len(graphics)!=1:raise ValueError('Missing graphics state')
   cgram=(root/(graphics[0]['stem']+'-cgram.bin')).read_bytes()
   colors=[int.from_bytes(cgram[(192+i)*2:(193+i)*2],'little') for i in range(16)]
   if palette is not None and palette!=colors:raise ValueError('Palette changed across capture')
   palette=colors;tiles,metadata=descriptor_tiles(rom,descriptor);pose=int(metadata['pose'][1:],16)
   frame={'descriptor':descriptor,'props':0x28,'origin_x':48,'origin_y':58,'parts':rom_parts(rom,pose),'tiles':base64.b64encode(tiles).decode('ascii')}
   evidence={'descriptor':descriptor,'prepared_frame':prepared,'displayed_frame':displayed,'pixels':report['screen']}
   return frame,evidence
  frames=[];evidence=[]
  for index,(case,prepared,displayed,descriptor) in enumerate(CASES):
   root=analysis/'keeper-throw-window'/'B' if case=='20' else analysis/'keeper-throw-offset'/case
   frame,entry=add_frame(root,baseline,prepared,displayed,descriptor,'0',False);frames.append(frame);evidence.append(entry)
  cycles['0']={'durations':DURATIONS,'frames':frames};reports['0']=evidence
  for direction,case in DIRECTED_CASES.items():
   name=case['name'];timeline=analysis/'keeper-directed-graphics'/name/'B'/'trial.jsonl'
   rows=[json.loads(line) for line in timeline.read_text(encoding='utf8').splitlines() if '"step"' in line]
   actual=[row for row in rows if row['script'] in (0xe625,0xe644)]
   expected=[descriptor for (_,_,_,descriptor),duration in zip(case['frames'],case['durations']) for _ in range(duration)]
   if [row['descriptor'] for row in actual]!=expected or any(row['direction']!=int(direction) for row in actual):raise ValueError('Unexpected directed timing')
   frames=[];evidence=[]
   for start,prepared,displayed,descriptor in case['frames']:
    root=analysis/'keeper-directed-graphics'/name/'B' if start==70 else analysis/'keeper-directed-offset'/name/str(start)
    control=analysis/'keeper-directed-graphics'/name/'NEUTRAL' if start==70 else analysis/'keeper-directed-neutral69'/name
    frame,entry=add_frame(root,control,prepared,displayed,descriptor,direction,True);frames.append(frame);evidence.append(entry)
   cycles[direction]={'durations':case['durations'],'frames':frames};reports[direction]=evidence
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps({'schema':'issd-keeper-throw-runtime-local/v2','width':96,'height':96,'palette':palette,'cycles':cycles},separators=(',',':'))+'\n',encoding='utf8')
 return {'schema':'issd-keeper-throw-runtime-audit/v2','rom_sha256':hashlib.sha256(rom).hexdigest(),'state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),'directions':reports,'limits':['One goalkeeper and one palette across three internal directions.','Some screen differences match earlier OAM pixels whose identity is unconfirmed.','The final hold is only the observed duration.','Team palette variants and screen direction mapping are not validated.','Local generated tiles are excluded from distribution.']}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--analysis',type=Path,default=Path('analysis'));parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--state',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
 result=build(args.analysis,args.rom,args.state,args.output);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('OK: fifteen verified goalkeeper descriptors exported locally')
