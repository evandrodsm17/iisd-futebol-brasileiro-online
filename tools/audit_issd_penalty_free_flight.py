"""Audit ordinary free-flight pairs before each captured penalty resolution."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path, trace_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Unexpected unheadered ROM')
    expected={0x61f73:bytes.fromhex('a5 07 18 65 28 85 07 e2 20 a5 09 65 2a 85 09 c2 20 a5 0f 18 65 2b 85 0f e2 20 a5 11 65 2d 85 11 c2 20 a5 0b 18 65 32 85 0b e2 20 a5 0d 65 34 85 0d c2 20 60'),
              0x61fb9:bytes.fromhex('a5 2b 18 6d 2e 17 85 2b e2 20 a5 2d 6d 30 17 85 2d')}
    for offset,data in expected.items():
        if rom[offset:offset+len(data)]!=data:raise ValueError('Unexpected native motion instructions')
    raw=trace_path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end':raise ValueError('Incomplete trace')
    vectors=[(i,e) for i,e in enumerate(events) if e.get('site')=='penalty_shot_vector']
    if len(vectors)!=8:raise ValueError('Unexpected shot count')
    samples=[];excluded=[]
    for n,(index,shot) in enumerate(vectors):
        segment=events[index:vectors[n+1][0] if n+1<len(vectors) else len(events)]
        resolutions=[e for e in segment if e.get('site')=='penalty_crossing_resolved' and (e['side'],e['round'],e['d'])==(shot['side'],shot['round'],shot['d'])]
        if len(resolutions)!=1:raise ValueError('Missing resolution')
        steps=[e for e in segment if e.get('site')=='penalty_shot_step' and e['frame']<=resolutions[0]['frame'] and (e['d'],e['side'],e['round'])==(shot['d'],shot['side'],shot['round'])]
        for before,after in zip(steps,steps[1:]):
            if after['frame']!=before['frame']+1 or not any(before[v] for v in ('dx','dy','dz')):continue
            positions=all(after[p]==(before[p]+before[v])&0xffff for p,v in (('px','dx'),('py','dy'),('pz','dz')))
            horizontal=all(after[v]==before[v] and after[v+'_ext']==before[v+'_ext'] for v in ('dx','dy'))
            z_before=before['dz'] | before['dz_ext']<<16;z_after=after['dz'] | after['dz_ext']<<16
            if not positions or not horizontal or z_after!=(z_before+0x20)&0xffffff:
                excluded.append({'frame':before['frame'],'side':shot['side'],'round':shot['round'], 'positions_match':positions,'horizontal_velocity_match':horizontal,'gravity_match':z_after==(z_before+0x20)&0xffffff})
                continue
            samples.append({'frame':before['frame'],'side':shot['side'],'round':shot['round'],
                            'position_low':[before['px'],before['py'],before['pz']],
                            'velocity':[before[v] | before[v+'_ext']<<16 for v in ('dx','dy','dz')],
                            'next_position_low':[after['px'],after['py'],after['pz']],
                            'next_velocity':[after[v] | after[v+'_ext']<<16 for v in ('dx','dy','dz')]})
    if len(samples)!=284 or len(excluded)!=8:raise ValueError(f'Unexpected captured subset: {len(samples)} / {len(excluded)}')
    return {'schema':'issd-penalty-free-flight/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'rom_offsets':['0x61f73','0x61fb9'],'gravity':0x20,'excluded_pairs':excluded,'samples':samples,
            'limits':['One synthetic shootout; only consecutive pairs before each observed resolution are included.',
                      'Eight differing pairs are excluded; the causes are not assumed.',
                      'Recorded position words are low 16 bits; their unrecorded upper bytes are not validated.',
                      'Collision, bounce, stopping, goalkeeper behavior and screen units are not covered.',
                      'ROM and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"OK: {len(result['samples'])} free-flight pairs; {len(result['excluded_pairs'])} differing pairs excluded")
