"""Audit observed input-to-actor-direction paths against the local ROM."""
import argparse
import hashlib
import json
from pathlib import Path


def read_rom(rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    if rom[header+0x5e35:header+0x5e3d] != bytes.fromhex('a8 b9 3a 96 29 0f 00 6b'):
        raise ValueError('Unexpected 80:DE35 routine')
    if rom[header+0x5d34:header+0x5d45] != bytes.fromhex('bd 13 00 29 0f 00 f0 09 a8 b9 13 96 29 ff 00 38 6b'):
        raise ValueError('Unexpected 80:DD34 routine')
    table=rom[header+0x963a:header+0x967a]
    if len(table)!=64: raise ValueError('Direction table truncated')
    dpad=rom[header+0x9613:header+0x9623]
    if len(dpad)!=16:raise ValueError('D-pad table truncated')
    return table,dpad


def analyze(rows, table, dpad_table):
    start=[r for r in rows if r.get('type')=='experiment_start']
    if len(start)!=1 or not any(r.get('type')=='session_end' and r.get('reason')=='experiment_window_complete' for r in rows):
        raise ValueError('Incomplete or ambiguous replay')
    hooks={r['address'] for r in rows if r.get('type')=='input_origin_hook_registration' and r.get('success')}
    required={'83F151','83F19F','83F1B1','80DD34','80DD45','80E770','80E7B0','80F455','80DE35'}
    if not required<=hooks: raise ValueError('Required hooks unavailable')
    actor=start[0]['p2'];events=[r for r in rows if r.get('type')=='input_origin_execution' and r['dp']==actor]
    records=[]
    for i,event in enumerate(events):
        if event['address']!='83F1B1':continue
        previous=[r for r in events[:i] if r['step']==event['step']]
        paths=[r['address'] for r in previous]
        transforms=[r for r in previous if r['address']=='80DE35']
        record={'step':event['step'],'actor':actor,'addresses':paths+['83F1B1'],
                'controller_held':event['controller_held'],'direction':event['direction'],'output_a':event['a']}
        if transforms:
            angle=transforms[-1]['a']
            if not isinstance(angle,int) or not 0<=angle<len(table):raise ValueError('Direction table index out of range')
            record.update({'path':'direction_lookup','input_index':angle,'expected_output':table[angle]&15,
                           'matches_lookup':event['a']==(table[angle]&15)})
        elif '80DD34' in paths:
            held=event.get('controller_held')
            if not isinstance(held,int):raise ValueError('Controller word unavailable')
            nibble=(held>>8)&15
            if nibble==0 and '80DD45' in paths:
                record.update({'path':'no_direction_fallback','dpad_nibble':nibble,
                               'matches_direction':event['a']==event['direction']})
            elif nibble!=0 and '80DD45' not in paths:
                record.update({'path':'held_direction_lookup','dpad_nibble':nibble,
                               'expected_output':dpad_table[nibble],
                               'matches_lookup':event['a']==dpad_table[nibble]})
            else:record['path']='other_or_unresolved'
        else:
            record['path']='other_or_unresolved'
        records.append(record)
    if not records:raise ValueError('No output observed for initial P2 actor')
    return {'observations':records,'limitations':['Path evidence covers only the monitored routines and selected replay window.',
            'The lookup index is a raw value; its exact physical meaning and producers require separate validation.',
            'Fallback conditions and branching should not be generalized to all game states.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();rom=a.rom.read_bytes();raw=a.trace.read_bytes()
    table,dpad=read_rom(rom)
    result=analyze([json.loads(x) for x in raw.splitlines() if x.strip()],table,dpad)
    result.update({'schema':'issd-input-origin/v1','source':{'trace':a.trace.as_posix(),'trace_sha256':hashlib.sha256(raw).hexdigest(),
                   'rom_sha256':hashlib.sha256(rom).hexdigest()},
                   'rom_offsets':{'lookup_routine':'0x5E35','dpad_routine':'0x5D34','direction_table':'0x963A',
                                  'dpad_table':'0x9613','header_adjusted':len(rom)%0x8000}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('observations:',len(result['observations']))


if __name__=='__main__':main()
