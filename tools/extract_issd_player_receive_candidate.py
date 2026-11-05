"""Map a ROM player reception candidate without assigning football semantics."""
import argparse,hashlib,json,re
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles,span

EXPECTED=(0xbbfe,0xbc34,0xbc6a,0xbc34,0xbbfe,0xbbc8,0xbb92,0xbbc8)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(rom_path,asm_path,root,state):
 raw=rom_path.read_bytes();head=len(raw)%0x8000
 if head not in (0,512) or hashlib.md5(raw[head:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 rom=raw[head:];asm=asm_path.read_text(encoding='utf8')
 labels={int(a,16):name for a,name in re.findall(r'^DATA_([0-9A-F]{6}):\s*\n\s*dw[^\n]*\n\s*incbin "Graphics/DynamicSprites/([^"/]+)"',asm,re.M)}
 table=span(rom,0x82deee,16);items=[]
 for direction,expected in enumerate(EXPECTED):
  desc=int.from_bytes(table[2*direction:2*direction+2],'little')
  if desc!=expected:raise ValueError('Descriptor table differs')
  _,meta=descriptor_tiles(rom,desc);source=int(meta['graphics_source'][1:],16);name=labels.get(source,'')
  if 'CatchBallWithKnee' not in name:raise ValueError('Unexpected source label')
  items.append({'direction_index':direction,'descriptor':desc,'pose_pointer':int(meta['pose'][1:],16),'graphics_source':source,'disassembly_asset':name,'row_bytes':meta['row_bytes']})
 route=r'CODE_848D08:.*?JSL\.l CODE_85F05B.*?JSL\.l CODE_80E48D.*?BNE\.b CODE_848D25.*?LDA\.w #DATA_82DEEE.*?LDY\.w #DATA_82E872\^\$8000.*?JMP\.w CODE_84E6AC'
 if not re.search(route,asm,re.S):raise ValueError('Expected assembly route not found')
 results=[]
 for case in ('Side','Up','Down'):
  def trial_rows(button):
   path=root/case/button/'trial.jsonl';data=[json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]
   header=next(x for x in data if x.get('type')=='session_start');samples={x['step']:x for x in data if 'step' in x}
   if set(samples)!=set(range(1,401)) or not any(x.get('type')=='session_end' and x['steps']==400 for x in data):raise ValueError('Incomplete input trial')
   return header,samples
  ah,aa=trial_rows('B');nh,nn=trial_rows('NEUTRAL');start=20 if case=='Side' else 70
  if ah['button']!='B' or nh['button']!='NEUTRAL' or ah['start']!=start or nh['start']!=start:raise ValueError('Unexpected trial setup')
  if any(aa[t]!=nn[t] for t in range(1,start)):raise ValueError('Paired baseline differs')
  if any(aa[t]['held_p1']!=0x8000 or nn[t]['held_p1']!=0 or aa[t]['selected']!=0x500 for t in range(start,start+6)):raise ValueError('Action input mismatch')
  for button in ('B','NEUTRAL'):
   folder=root/case/button;trace=folder/'keeper-transfers.jsonl';trial=folder/'trial.jsonl'
   rows=[json.loads(x) for x in trace.read_text(encoding='utf8').splitlines() if x.strip()]
   if not any(x.get('type')=='session_end' for x in rows):raise ValueError('Incomplete trace')
   events=[x for x in rows if x.get('type')=='receive_hook']
   results.append({'case':case,'button':button,'receive_callbacks':len(events),'trace_sha256':sha(trace),'trial_sha256':sha(trial)})
 return {'schema':'issd-player-receive-candidate/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'disassembly_sha256':sha(asm_path),'state_sha256':sha(state),
  'descriptor_table':'$82:DEEE','selection_entry':'$84:8D08','alternate_branch':'$84:8D25','directions':items,'replays':results,
  'limitations':['Disassembly filenames are labels; knee or chest reception is not proven visually or semantically.',
   'Six recorded replays produced no callbacks; no independent positive-control event establishes hook coverage.',
   'No OAM/VRAM/CGRAM/PPU reference or timing was captured for these descriptors.',
   'Goalkeeper teammate selection and arrival/possession conditions remain unverified.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('analysis/keeper-receiver-trace'));p.add_argument('--asm',type=Path,default=Path('YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'));p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=extract(a.rom,a.asm,a.root,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: eight candidate direction entries; six replay summaries')
if __name__=='__main__':main()
