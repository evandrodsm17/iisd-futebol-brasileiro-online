"""Verify the captured penalty contact-response subroutine against the local ROM."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

MASK=0xffffff

def model(before):
    difference=(before['target_vz']-before['source_vz'])&MASK
    carry=difference&1
    rotated=((difference&0xffff)>>1)|(0x8000 if difference&0x800000 else 0)
    upper=((~(((difference>>16)<<8)|(rotated>>8)))+carry)&0xffff
    low=((~rotated)+1)&0xff
    return {'target_y':(before['target_y']&0xff)|(((before['peer_y']+4)&0xffff)<<8),
            'target_vx':(before['target_vx']+before['source_vx'])&MASK,'target_vy':0,
            'target_vz':((upper<<8)|low)&MASK}


def audit(rom_path,directory,prior_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    expected=bytes.fromhex('0b a5 36 5b a6 1a a5 0c 18 69 04 00 9d 0c 00 9e 32 00 9e 33 00 ad 02 17 5b bd 2b 00 38 e5 2b 9d 2b 00 e2 20 bd 2d 00 e5 2d 9d 2d 00 c2 20 bd 2c 00 c9 00 80 7e 2b 00 bd 2c 00 49 ff ff 9d 2c 00 e2 20 bd 2b 00 49 ff 1a 9d 2b 00 c2 20 bd 2c 00 69 00 00 9d 2c 00 bd 28 00 18 65 28 9d 28 00 e2 20 bd 2a 00 65 2a 9d 2a 00 c2 20 2b 60')
    if rom[0x62500:0x62500+len(expected)]!=expected:raise ValueError('Unexpected response instructions')
    raw=(directory/'response.jsonl').read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in events):raise ValueError('Incomplete response capture')
    driver_path,=directory.glob('issd-auto-probe-*.jsonl');driver_raw=driver_path.read_bytes();driver=[json.loads(line) for line in driver_raw.splitlines()]
    configs=[e for e in driver if e.get('type')=='penalty_direction_config']
    if len(configs)!=1 or configs[0].get('direction')!='Right' or configs[0].get('controllers')!='p1' or not any(e.get('type')=='synthetic_clock' for e in driver) or not any(e.get('type')=='synthetic_score' for e in driver) or not any(e.get('type')=='session_end' for e in driver):raise ValueError('Unexpected replay setup')
    prior_raw=prior_path.read_bytes();prior=json.loads(prior_raw)
    if prior['schema']!='issd-penalty-flight-differences/v1':raise ValueError('Unexpected prior report')
    expected_contacts=[e for e in prior['results'] if e['route']=='object_contact']
    before=[e for e in events if e.get('site')=='before'];after=[e for e in events if e.get('site')=='after']
    if len(before)!=2 or len(after)!=2 or len(expected_contacts)!=2:raise ValueError('Unexpected response count')
    cases=[]
    for a,b,prior_case in zip(before,after,expected_contacts):
        if any(a[k]!=b[k] for k in ('frame','side','round','target','flags')) or any(a[k]!=prior_case[k] for k in ('frame','side','round')) or a['peer']!=prior_case['collision_object'] or a['contact']!=prior_case['contact_object'] or a['target']!=0x700:raise ValueError('Unexpected object chain')
        result=model(a)
        if any(result[k]!=b[k] for k in result):raise ValueError('Response mismatch')
        cases.append({'frame':a['frame'],'side':a['side'],'round':a['round'],'peer':a['peer'],'target':a['target'],'source':a['source'],
                      'input':{k:a[k] for k in ('peer_y','target_y','target_vx','target_vy','target_vz','source_vx','source_vz')},'output':result})
    return {'schema':'issd-penalty-contact-response/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'prior_sha256':hashlib.sha256(prior_raw).hexdigest(),
            'rom_offset':'0x62500','cases':cases,
            'limits':['One synthetic replay and two observed contacts with the same numerical motion values.',
                      'Contact detection, object selection, control mapping and other response branches are not established.',
                      'Carry behavior follows the static 65C816 instructions; edge-case tests are not captured evidence.',
                      'ROM and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','directory','prior','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.directory,args.prior)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 2 native contact responses match the 24-bit model')
