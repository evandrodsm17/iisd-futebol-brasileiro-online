"""Verify pass-detail tile selection under isolated synthetic actor variants."""
import argparse,hashlib,json
from pathlib import Path
from compare_issd_action_trials import load,signature
from render_issd_descriptor_sprite import descriptor_tiles
from extract_issd_catalog import EXPECTED_MD5


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

def audit(root,rom_path,state):
 rom=rom_path.read_bytes()
 if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
 cases={};baseline=None
 for name,variant in [('natural',18),('0',0),('14',14),('30',30)]:
  directory=root/name;paths=list(directory.glob('issd-auto-probe-*.jsonl'))
  if len(paths)!=1:raise ValueError('Missing trace')
  rows=read(paths[0]);marks=[x for x in rows if x.get('type')=='synthetic_kit_variant']
  if name=='natural':
   if marks:raise ValueError('Unexpected override')
  elif len(marks)!=1 or marks[0]['address']!=0x1956 or marks[0]['value']!=variant:raise ValueError('Missing synthetic marker')
  trace=load(paths[0]);before=[i for i in sorted(trace['samples']) if 0<=i<480]
  if len(before)<240:raise ValueError('Incomplete baseline')
  if baseline is None:baseline=trace
  elif any(signature(trace['samples'][i],True)!=signature(baseline['samples'][i],True) for i in before):raise ValueError('Logged baseline mismatch')
  draws=read(directory/'slide-draw.jsonl');captures={x['frame']:x for x in read(directory/'slide-poses.jsonl')};samples=[]
  for f in (4276,4278):
   g=next(r for r in draws if r.get('type')=='body_geometry' and r['frame']==f-1 and r['object']==0x1900)
   actor={'type':g['actor_type'],'kit_variant':g['kit_variant'],'uniform_selector':g['uniform_selector'],'object_flags':g['object_flags']}
   if actor['kit_variant']!=variant or actor['type']!=6:raise ValueError('Actor variant mismatch')
   tiles,meta=descriptor_tiles(rom,g['descriptor'],actor);shown=captures[f+1];vram=(directory/(shown['stem']+'-vram.bin')).read_bytes()
   base=((shown['obsel']&7)<<9)+(((shown['obsel']&0x18)+8)<<5);address=((base+((g['tile_base']+23)&255))&2047)*32
   actual=vram[address:address+32]
   if actual!=tiles[23*32:24*32] or meta['detail']!=4:raise ValueError('Detail mismatch')
   samples.append({'frame':f,'descriptor':g['descriptor'],'actor':actor,'detail_byte':meta['detail'],'detail_source':meta['detail_source'],'tile_sha256':hashlib.sha256(actual).hexdigest()})
  cases[name]={'synthetic':name!='natural','variant':variant,'trace_sha256':trace['sha256'],'draw_sha256':sha(directory/'slide-draw.jsonl'),'samples':samples}
 return {'schema':'issd-pass-detail-variants/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),'cases':cases,'limitations':['Three variants were changed synthetically in isolated replay RAM; natural variant 18 was not changed.','One actor, team, direction, type and action; no-write colors and other contexts are not validated.','Matching logged fields is not equality of all emulator state.','ROM and graphics captures remain local.']}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.root,a.rom,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('pass detail: four observed variants match ROM')
