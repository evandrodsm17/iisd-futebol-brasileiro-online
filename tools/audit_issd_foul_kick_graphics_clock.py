"""Audit the captured foul kick animation descriptors and sampled match clock."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root,state):
    frames={}; traces={}
    for case in ('A','NEUTRAL'):
        directory=root/case
        paths=list(directory.glob('issd-auto-probe-*.jsonl'))
        paths=[p for p in paths if not p.name.endswith('-graphics.jsonl')]
        if len(paths)!=1: raise ValueError('Expected one input trace')
        rows=read(paths[0]);traces[case]={r['step']:r for r in rows if 'actors' in r}
        if not any(r.get('type')=='session_end' and r['steps']==5401 for r in rows):raise ValueError('Incomplete replay')
        for kind,address in (('synthetic_foul_setting',0x1e50),('synthetic_referee',0x1e58)):
            found=[r for r in rows if r.get('type')==kind]
            if len(found)!=1 or found[0]['address']!=address or found[0]['value']!=0:raise ValueError('Missing override marker')
        frames[case]={r['frame']:r for r in read(directory/'defense-opponent.jsonl') if r['type']=='frame_end'}
        if set(frames[case])!=set(range(4274,5001)):raise ValueError('Incomplete frame data')
    base=traces['NEUTRAL']; a=traces['A'];steps=sorted(s for s in base if s<4801)
    if steps!=sorted(s for s in a if s<4801) or any(a[s]!=base[s] for s in steps):raise ValueError('Different logged baseline')
    if any(frames['A'][f]['clock_16d0']!=0x451 for f in range(4282,4668)):
        raise ValueError('Unexpected action clock')
    if frames['A'][4612]['phase']!=4 or frames['A'][4613]['phase']!=0 or frames['A'][4668]['clock_16d0']!=0x450:
        raise ValueError('Unexpected restart or clock transition')
    if any(frames['NEUTRAL'][f]['clock_16d0']!=0x451 or frames['NEUTRAL'][f]['phase']!=4 for f in range(4282,5001)):
        raise ValueError('Unexpected control clock')
    directory=root/'A';paths=list(directory.glob('*-graphics.jsonl'))
    if len(paths)!=1:raise ValueError('Missing graphics manifest')
    graphics=read(paths[0])
    if [r['step'] for r in graphics]!=list(range(4796,4832)):raise ValueError('Incomplete graphics window')
    if any(r['actor']['address']!=0x1200 or r['frame']!=r['step']-205 for r in graphics):raise ValueError('Unexpected actor or frame alignment')
    for r in graphics:
        for key,size in [('oam_mirror',544),('oam_ppu',544),('vram',65536),('cgram_ppu',512)]:
            if not r.get(key) or (directory/r[key]).stat().st_size!=size:raise ValueError(f'Missing capture {key}')
        if not r.get('screenshot') or not (directory/r['screenshot']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Missing screenshot')
    changes=[];last=None
    for r in graphics:
        actor=r['actor']; key=(actor['animation_script'],actor['descriptor'],actor['direction'])
        if key!=last:
            changes.append({'frame':r['frame'],'step':r['step'],'script':key[0],'descriptor':key[1],'direction':key[2]});last=key
    expected=[(0xd69a,0xaa85,3),(0xcf9f,0xa791,3),(0xcf9f,0xa79a,3),(0xcf9f,0xa7a3,3),(0xcf9f,0xa7ac,3),
              (0xd1c5,0xad4c,3),(0xd1c5,0xad55,3),(0xd1c5,0xad5e,3),(0xd1c5,0xad67,3),(0xd1c5,0xad3a,4)]
    if [(x['script'],x['descriptor'],x['direction']) for x in changes]!=expected:raise ValueError('Unexpected descriptor sequence')
    return {'schema':'issd-foul-kick-graphics-clock/v1','declared_state_sha256':sha(state),'baseline_sample_count':len(steps),
      'action_probe_sha256':sha(root/'A'/'defense-opponent.jsonl'),'control_probe_sha256':sha(root/'NEUTRAL'/'defense-opponent.jsonl'),
      'graphics_manifest_sha256':sha(paths[0]),'capture_frames':[4591,4626],'graphics_count':len(graphics),
      'clock':{'raw_bcd':0x451,'foul_frames':[4282,4612],'phase_zero_frame':4613,'first_action_decrement_frame':4668,'next_raw_bcd':0x450,'control_constant_through':5000},
      'observed_descriptor_changes':changes,
      'limitations':['One A-button foul restart; referee and foul setting were synthetic RAM overrides.',
        'OAM/VRAM/CGRAM and screenshots were captured locally, but individual actor OAM slots and pixel composition have not been validated.',
        'Descriptor and graphics samples are same-frame records; PPU upload timing requires independent alignment.',
        'Clock is observed in this specific match; do not generalize to all events or modes.',
        'Logged baseline equality does not establish equality of unobserved state.',
        'Save-state identity is declared, not authenticated by traces.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root,a.state);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('foul animation and clock: OK (36 captures)')
