"""Verify type-5 vertical lookup tables against ROM and controlled hold replays."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

def sha(data):return hashlib.sha256(data).hexdigest()
def audit(rom,trace,state,assembly):
 data=rom.read_bytes();header=len(data)%0x8000
 if header not in (0,512) or hashlib.md5(data[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM revision')
 source=assembly.read_text(encoding='utf8')
 fragment=source.split('CODE_839702:',1)[1].split('CODE_839712:',1)[0]
 for token in ('LDA.w $0456','LDA.w DATA_81A24B,y','STA.b $36,x','LDA.w DATA_81A263,y','STA.b $34,x'):
  if token not in fragment:raise ValueError('Unexpected disassembly sequence')
 words=[]
 for i in range(12):
  hi=int.from_bytes(data[header+0xa24b+i*2:header+0xa24d+i*2],'little');lo=int.from_bytes(data[header+0xa263+i*2:header+0xa265+i*2],'little');words.append({'parameter':i,'integer_word':hi,'fraction_word':lo})
 raw=trace.read_bytes();rows=[json.loads(s) for s in raw.splitlines()];cases={r['trial']:r for r in rows if r['type']=='case'}
 if len(cases)!=15 or any(sum(r['type']=='frame' and r['trial']==i for r in rows)!=45 for i in range(1,16)):raise ValueError('Incomplete hold sweep')
 trials=[];seen=set()
 for i,c in sorted(cases.items()):
  hooks=[r for r in rows if r['type']=='hook' and r['trial']==i and r['site']=='85F89B']
  if len(hooks)!=1:raise ValueError('Unexpected release count')
  h=hooks[0];p=h['y'];samples=[r for r in rows if r['type']=='frame' and r['trial']==i and r['step']==h['step']]
  if not 0<=p<12 or len(samples)!=1:raise ValueError('Bad parameter or missing sample')
  f=samples[0];value=words[p]
  if f['ballType']!=5 or f['carrier']!=0 or f['vz']!=value['integer_word'] or f['vzFrac']!=value['fraction_word']:raise ValueError(f'Mismatch in trial {i}')
  seen.add(p);trials.append({'trial':i,'held_frames':c['heldFrames'],'release_step':h['step'],'parameter':p,'button_still_held':bool(h['held']&64)})
 if seen!=set(range(12)):raise ValueError('Not all parameters observed')
 return {'schema':'issd-type5-vertical-table/v1','rom_sha256':sha(data[header:]),'trace_sha256':sha(raw),'state_sha256':sha(state.read_bytes()),'disassembly_sha256':sha(assembly.read_bytes()),'routine':'83:9702','type_dispatch':'83:956E type 5 to 83:96E7','rom_offsets':{'integer_words':'0x00A24B','fraction_words':'0x00A263'},'table':words,'trials':trials,'limits':['The table is a component of type-5 initialization, not the full trajectory or proof that all X actions select type 5.','Frame-end equality is observed for this actor, state, direction and weather only.','Native coordinates and velocity words are not mapped to browser units.','ROM, screenshots and saved state are not included.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('trace',type=Path);p.add_argument('state',type=Path);p.add_argument('assembly',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=audit(a.rom,a.trace,a.state,a.assembly);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK: 12 ROM table pairs match 15 release observations')
if __name__=='__main__':main()
