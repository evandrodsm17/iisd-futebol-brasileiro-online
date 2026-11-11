"""Audit the rise to the apex of a previously captured type-3 ball release."""
import argparse,collections,hashlib,json
from pathlib import Path
from audit_issd_shot_airborne import audit as audit_base

def raw(r,integer,fraction):return (r[integer]<<16)|r[fraction]
def signed(n):return n-2**32 if n&0x80000000 else n

def audit(root,baseline,rom):
 verified=audit_base(root,baseline,rom)
 events=[json.loads(line) for line in (root/'keeper-transfers.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
 groups=collections.defaultdict(list)
 for r in events:
  if r.get('type')=='ball_vertical' and 4279<=r['frame']<=4343:groups[r['frame']].append(r)
 sequence=[];previous=None
 for frame,items in sorted(groups.items()):
  if [r['address'] for r in items]!=['83941F','83942E','83882A','838863','838865']:raise ValueError(f'Incomplete hooks at {frame}')
  entry,accel,before,store,after=items
  if any(r['ball_type']!=3 or r['xreg']!=0x400 or r['link_a6']!=0 for r in items):raise ValueError('Unexpected ball context')
  position=raw(accel,'z','z_frac');velocity=raw(accel,'vz','vz_frac');newv=(velocity+accel['gravity'])&0xffffffff;newz=(position+newv)&0xffffffff
  if raw(before,'vz','vz_frac')!=newv or raw(after,'z','z_frac')!=newz or store['a']!=newz>>16:raise ValueError('Integration mismatch')
  if previous and (position,velocity)!=(previous['position_after_raw'],previous['velocity_after_raw']):raise ValueError('Trajectory is not consecutive')
  sequence.append({'frame':frame,'position_before_raw':position,'velocity_before_raw':velocity,'gravity':accel['gravity'],'position_after_raw':newz,'velocity_after_raw':newv})
  previous=sequence[-1]
 if len(sequence)!=64 or sequence[0]['frame']!=4279 or sequence[-1]['frame']!=4343:raise ValueError('Unexpected apex capture coverage')
 peak=min(signed(s['position_after_raw']) for s in sequence)
 if signed(sequence[-1]['velocity_after_raw'])!=0 or peak!=-220.5*65536:raise ValueError('Unexpected apex')
 return {'schema':'issd-natural-shot-peak/v1','source_airborne_audit':verified,'rise_updates':len(sequence),'first_update_frame':sequence[0]['frame'],'peak_frames':[s['frame'] for s in sequence if signed(s['position_after_raw'])==peak],'native_initial_velocity':signed(sequence[0]['velocity_before_raw'])/65536,'native_gravity':sequence[0]['gravity']/65536,'native_peak_height':-peak/65536,'updates':sequence,'native_to_web_conditional_scale':38/52,'conditional_web_peak':(-peak/65536)*(38/52),'limitations':['One captured X-button action with one actor, direction, weather and ball type; it is not established as a universal shot or kick.','The 38/52 factor is a presentation hypothesis, not a validated physical conversion.','The first 64 observed updates are consecutive even though frame 4280 has no matching hooks; no update is fabricated.','The later trajectory changes and must be audited independently before interpreting its outcome.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--baseline',required=True,type=Path);p.add_argument('--rom',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();r=audit(a.root,a.baseline,a.rom);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',r['rise_updates'],'consecutive native updates; peak',r['native_peak_height'],'at',r['peak_frames'])
if __name__=='__main__':main()
