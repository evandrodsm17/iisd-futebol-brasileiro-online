"""Audit native penalty movement gates with directly captured 24-bit states."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

MASK=0xffffff
FIELDS=('x','y','z','vx','vy','vz')

def audit(rom_path, directory):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    expected={0x61fa7:bytes.fromhex('20 73 9f a5 0c 38 e9 02 00 85 12 a5 10 30 03 20 f9 9f'),
              0x61ff9:bytes.fromhex('a5 0c f0 2a a5 33 30 14 a5 32 38 e9 08 00 85 32'),
              0x62027:bytes.fromhex('a5 08 f0 2a a5 29 30 14 a5 28 38 e9 08 00 85 28'),
              0x62056:bytes.fromhex('a5 2b 10 04 49 ff ff 1a c9 40 00 b0 15 a5 10 10 04 49 ff ff 1a c9 02 00 b0 08 64 2b 64 2c 64 10 64 0e a5 28 10 04 49 ff ff 1a c9 40 00 b0 08 a5 10 d0 19 64 28 64 29 a5 32 10 04 49 ff ff 1a c9 40 00 b0 08 a5 10 d0 04 64 32 64 33 60')}
    for offset,code in expected.items():
        if rom[offset:offset+len(code)]!=code:raise ValueError(f'Unexpected ROM instructions at {offset:x}')
    raw=(directory/'gates.jsonl').read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in events):raise ValueError('Incomplete gate trace')
    driver_path,=directory.glob('issd-auto-probe-*.jsonl');driver_raw=driver_path.read_bytes();driver=[json.loads(line) for line in driver_raw.splitlines()]
    config=[e for e in driver if e.get('type')=='penalty_direction_config']
    if len(config)!=1 or config[0].get('direction')!='Right' or config[0].get('controllers')!='p1' or not any(e.get('type')=='synthetic_score' for e in driver) or not any(e.get('type')=='synthetic_clock' for e in driver) or not any(e.get('type')=='session_end' for e in driver):raise ValueError('Unexpected replay setup')
    frames=(9850,9851,10276,10293,11236,11253,11682,11683)
    def single(group,name,required=True):
        matches=[e for e in group if e.get('site')==name]
        if len(matches)>1 or (required and not matches):raise ValueError(f'Unexpected {name} count')
        return matches[0] if matches else None
    def abs16(value):
        word=value&0xffff
        return (-word)&0xffff if word&0x8000 else word
    results=[]
    for frame in frames:
        group=[e for e in events if e.get('frame')==frame]
        start=single(group,'move_start');end=single(group,'move_end')
        if start['gravity']!=32 or any(start[k]!=end[k] for k in ('side','round','d','gravity')):raise ValueError('Mismatched event context')
        state={k:start[k] for k in FIELDS}
        for p,v in (('x','vx'),('y','vy'),('z','vz')):state[p]=(state[p]+state[v])&MASK
        height=state['z']>>8;grounded=not height&0x8000
        flags={'friction_x':grounded and state['x']>>8!=0,'friction_y':grounded and state['y']>>8!=0,'bounce':grounded and height!=0}
        if bool(single(group,'friction_start',False))!=grounded or bool(single(group,'bounce',False))!=flags['bounce']:raise ValueError('Branch hook mismatch')
        for field,enabled in (('vx',flags['friction_x']),('vy',flags['friction_y'])):
            if enabled:state[field]=(state[field]+(8 if state[field]&0x8000 else -8))&MASK
        state['vz']=(state['vz']+start['gravity'])&MASK
        if flags['bounce']:
            if state['vz']>0x7fff:raise ValueError('Out of observed bounce domain')
            state['z']&=0xff;state['vz']=(-int(state['vz']/2))&MASK
        if any(state[k]!=end[k] for k in FIELDS):raise ValueError(f'Motion mismatch at {frame}')
        stop=single(group,'stop_start',False);after_stop=single(group,'stop_end',False)
        if bool(stop)!=bool(after_stop):raise ValueError('Incomplete stop hooks')
        if stop:
            if any(stop[k]!=end[k] for k in FIELDS):raise ValueError('Unexpected intermediate stop state')
            if abs16(state['vz'])<0x40 and abs16(state['z']>>8)<2:state['vz']=0;state['z']=0
            if abs16(state['vx'])<0x40 and state['z']>>8==0:state['vx']=0
            if abs16(state['vy'])<0x40 and state['z']>>8==0:state['vy']=0
            if any(state[k]!=after_stop[k] for k in FIELDS):raise ValueError('Stop mismatch')
        results.append({'frame':frame,'side':start['side'],'round':start['round'],
                        'before':{k:start[k] for k in FIELDS},'gravity':start['gravity'],'branches':flags,
                        'after_motion':{k:end[k] for k in FIELDS},'stop_after':bool(stop),
                        'after_stop':{k:after_stop[k] for k in FIELDS} if after_stop else None})
    if sum(r['branches']['bounce'] for r in results)!=4 or sum(r['stop_after'] for r in results)!=2:raise ValueError('Unexpected branch counts')
    return {'schema':'issd-penalty-ground-gates/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'results':results,
            'limits':['One synthetic replay; only eight previously selected frames were instrumented.',
                      'Contact with other objects may occur after move_end and is not predicted by this model.',
                      'Stopping is called only by certain native scripts; this audit does not select them.',
                      'Bounce model is limited to the observed nonnegative velocity domain.',
                      'ROM and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','directory','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.directory)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 8 full 24-bit movement states; 4 bounces and 2 stop calls')
