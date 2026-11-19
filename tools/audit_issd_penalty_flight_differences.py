"""Correlate eight differing penalty steps with contact and friction evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

MASK=0xffffff

def audit(rom_path, motion_dir, contact_dir, prior_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    for offset,data in {0x61fa7:bytes.fromhex('20 73 9f a5 0c 38 e9 02 00 85 12 a5 10 30 03 20 f9 9f'),
                        0x61ff9:bytes.fromhex('a5 0c f0 2a a5 33 30 14 a5 32 38 e9 08 00 85 32'),
                        0x62027:bytes.fromhex('a5 08 f0 2a a5 29 30 14 a5 28 38 e9 08 00 85 28'),
                        0x61fd2:bytes.fromhex('64 10 a5 2b a0 02 00 22 4c 8b 80 85 2b')}.items():
        if rom[offset:offset+len(data)]!=data:raise ValueError(f'Unexpected ROM bytes: {offset:x}')
    raw=(motion_dir/'mode-hooks.jsonl').read_bytes();other=(contact_dir/'mode-hooks.jsonl').read_bytes();prior_raw=prior_path.read_bytes()
    prior=json.loads(prior_raw)
    if prior['schema']!='issd-penalty-free-flight/v1' or prior['trace_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('Mismatched prior audit')
    drivers=[]
    for directory in (motion_dir,contact_dir):
        path,=directory.glob('issd-auto-probe-*.jsonl');drivers.append(hashlib.sha256(path.read_bytes()).hexdigest())
    if drivers[0]!=drivers[1]:raise ValueError('Replays use different driver trace')
    events=[json.loads(line) for line in raw.splitlines()];hooks=[json.loads(line) for line in other.splitlines()]
    if any(e[0].get('site')!='session_start' or e[-1].get('site')!='session_end' for e in (events,hooks)):raise ValueError('Incomplete trace')
    results=[]
    for excluded in prior['excluded_pairs']:
        frame,side,round_no=(excluded[k] for k in ('frame','side','round'))
        def find(frame_no):
            found=[e for e in events if e.get('site')=='penalty_shot_step' and (e['frame'],e['side'],e['round'],e['d'])==(frame_no,side,round_no,0x700)]
            if len(found)!=1:raise ValueError('Unexpected motion record')
            return found[0]
        a,b=find(frame),find(frame+1)
        def vel(e,k):return e[k] | e[k+'_ext']<<16
        contacts=[e for e in events if e.get('site')=='penalty_contact_action' and (e['frame'],e['side'],e['round'])==(frame,side,round_no)]
        collisions=[e for e in events if e.get('site')=='penalty_collision_selected' and (e['frame'],e['side'],e['round'],e['linked_object'])==(frame-1,side,round_no,0x700)]
        ground=[e for e in hooks if e.get('site')=='penalty_ground_contact' and (e['frame'],e['side'],e['round'],e['d'])==(frame,side,round_no,0x700)]
        if contacts:
            if len(contacts)!=1 or len(collisions)!=1 or contacts[0]['linked_object']!=collisions[0]['d'] or ground:raise ValueError('Unexpected contact chain')
            results.append({'frame':frame,'side':side,'round':round_no,'route':'object_contact',
                            'collision_object':collisions[0]['d'],'contact_object':contacts[0]['d']})
            continue
        if len(ground)>1:raise ValueError('Duplicate ground hooks')
        friction=[]
        for v in ('dx','dy'):
            current=vel(a,v);new=vel(b,v);decelerated=(current+(8 if current&0x8000 else -8))&MASK
            if new==current:friction.append(False)
            elif new==decelerated:friction.append(True)
            else:raise ValueError('Unexplained horizontal velocity')
        if not any(friction):raise ValueError('No horizontal damping observed')
        if any(b[p]!=(a[p]+a[v])&0xffff for p,v in (('px','dx'),('py','dy'))):raise ValueError('Unexpected horizontal motion')
        z_after=(vel(a,'dz')+0x20)&MASK
        if ground:
            g=ground[0]
            if not 0<g['height']<0x8000 or g['gravity']!=0x20 or g['velocity']!=(z_after&0xffff):raise ValueError('Ground hook mismatch')
            if z_after>0x7fff or b['pz']!=((a['pz']+a['dz'])&0xff) or vel(b,'dz')!=(-((z_after&0xffff)//2))&MASK:raise ValueError('Bounce mismatch')
            kind='ground_contact'
        else:
            if b['pz']!=(a['pz']+a['dz'])&0xffff or vel(b,'dz')!=z_after:raise ValueError('Unexpected vertical motion')
            kind='damping_only'
        results.append({'frame':frame,'side':side,'round':round_no,'route':kind,
                        'position_low':[a['px'],a['py'],a['pz']],'velocity':[vel(a,v) for v in ('dx','dy','dz')],
                        'next_position_low':[b['px'],b['py'],b['pz']],'next_velocity':[vel(b,v) for v in ('dx','dy','dz')],
                        'friction_x':friction[0],'friction_y':friction[1]})
    if [sum(r['route']==k for r in results) for k in ('damping_only','ground_contact','object_contact')]!=[2,4,2]:raise ValueError('Unexpected route counts')
    return {'schema':'issd-penalty-flight-differences/v1','motion_sha256':hashlib.sha256(raw).hexdigest(),
            'contact_sha256':hashlib.sha256(other).hexdigest(),'driver_sha256':drivers[0],
            'prior_sha256':hashlib.sha256(prior_raw).hexdigest(),'results':results,
            'limits':['One synthetic match, with a separately instrumented deterministic replay.',
                      'Damping gates are inferred from before/after values, not directly instrumented.',
                      'Ground-contact hooks are in the separately instrumented replay; context and driver match.',
                      'The two contact cases link objects but do not by themselves prove all keeper behavior.',
                      'Position upper bytes, unobserved edge cases, ROM and raw captures remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','motion','contact','prior','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.motion,args.contact,args.prior)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 2 damping-only, 4 ground-contact and 2 linked-object contact cases')
