"""Audit observed alternate action state dispatch and release calls."""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED=('8496B8','8496CF','8496D4','8496E5','85F438','85F45F','85F871','85F89B','85F8B9')


def verify_rom(rom):
    header=len(rom)%0x8000
    if header not in (0,512):raise ValueError('Unsupported ROM header')
    for offset,expected in ((0xbeb8,bytes.fromhex('cf96d496cf963000')),
                            (0xbec0,bytes.fromhex('e596e596e5963000'))):
        if rom[header+offset:header+offset+8]!=expected:raise ValueError('State dispatch row differs from expected ROM')
    return header


def analyze(rows):
    starts=[r for r in rows if r.get('type')=='experiment_start']
    if len(starts)!=1 or not any(r.get('type')=='session_end' and r.get('reason')=='experiment_window_complete' for r in rows):
        raise ValueError('Incomplete or ambiguous replay')
    hooks={r['address'] for r in rows if r.get('type')=='alternate_hook_registration' and r.get('success')}
    if not set(REQUIRED)<=hooks:raise ValueError('Required hooks unavailable')
    actor=starts[0]['p2']; trigger=starts[0]['step']
    events=[{k:r.get(k) for k in ('step','frame','address','dp','a','x','y','field_6e','timer_70','ball_type','link_a4','link_a6')}
            for r in rows if r.get('type')=='alternate_execution' and r.get('dp')==actor]
    essential=('8496B8','8496D4','8496E5','85F438','85F45F','85F871')
    pos=0
    for wanted in essential:
        while pos<len(events) and events[pos]['address']!=wanted:pos+=1
        if pos==len(events):raise ValueError('Observed event sequence incomplete')
        pos+=1
    samples=[]
    for r in rows:
        elapsed=r.get('step',0)-trigger
        if r.get('type') or elapsed<479 or elapsed>505 or 'actors' not in r:continue
        matches=[a for a in r['actors'] if a['address']==actor]
        if len(matches)!=1:raise ValueError('Actor missing or duplicated')
        a=matches[0]
        samples.append({'elapsed':elapsed,'state':a['state'],'script':a['script'],
                        'descriptor':a['descriptor'],'ball_type':r['ball']['type'],'link_a6':r['link_a6']})
    if not samples:raise ValueError('Missing actor samples')
    return {'actor':actor,'events':events,'samples':samples,
            'limitations':['Event and state evidence applies only to this scenario and actor.',
                           'Pre-instruction callbacks do not alone prove every intermediate write.',
                           'Action name, all branch conditions and ball physics remain unverified.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();rom=a.rom.read_bytes();raw=a.trace.read_bytes()
    header=verify_rom(rom);result=analyze([json.loads(l) for l in raw.splitlines() if l.strip()])
    result.update({'schema':'issd-alternate-action/v1','source':{'trace':a.trace.as_posix(),
        'trace_sha256':hashlib.sha256(raw).hexdigest(),'rom_sha256':hashlib.sha256(rom).hexdigest()},
        'rom_offsets':{'state_0160':'0xBEB8','state_0168':'0xBEC0','header_adjusted':header}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('events:',len(result['events']),'samples:',len(result['samples']))


if __name__=='__main__':main()
