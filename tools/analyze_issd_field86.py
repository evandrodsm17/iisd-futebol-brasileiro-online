"""Check observed 80:E48D field writes against its local ROM lookup table."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROUTINE=bytes.fromhex('38 e5 2e 29 07 00 0a a8 b9 b2 96 85 86 6b')


def read_table(rom):
    header=len(rom)%0x8000
    if header not in (0,512):raise ValueError('Unsupported ROM header')
    if rom[header+0x648d:header+0x649b]!=EXPECTED_ROUTINE:
        raise ValueError('ROM routine does not match 80:E48D')
    data=rom[header+0x96b2:header+0x96c2]
    if len(data)!=16:raise ValueError('ROM table truncated')
    return [int.from_bytes(data[i:i+2],'little') for i in range(0,16,2)]


def evaluate(entry, result, table):
    if entry['step']!=result['step'] or entry['dp']!=result['dp']:
        raise ValueError('Entry and return do not belong to same step and actor')
    if entry['direction']!=result['direction']:raise ValueError('Direction changed inside routine')
    delta=(entry['a']-entry['direction'])&7
    expected=table[delta]
    return {'step':entry['step'],'actor':entry['dp'],'input_a':entry['a'],
            'field_84':entry['field_84'],'direction':entry['direction'],
            'difference_mod_8':delta,'table_byte_offset':delta*2,
            'field_86_before':entry['field_86'],'field_86_after':result['field_86'],
            'result_a':result['a'],'result_y':result['y'],
            'matches_rom_formula':result['field_86']==expected and result['a']==expected and result['y']==delta*2}


def analyze(rows,table):
    starts=[r for r in rows if r.get('type')=='experiment_start']
    if len(starts)!=1 or not any(r.get('type')=='session_end' and r.get('reason')=='experiment_window_complete' for r in rows):
        raise ValueError('Incomplete or ambiguous replay')
    registrations={r['address'] for r in rows if r.get('type')=='selection_hook_registration' and r.get('success')}
    if not {'80E48D','80E49A'} <= registrations:raise ValueError('Field-write hooks unavailable')
    actor=starts[0]['p2'];events=[r for r in rows if r.get('type')=='selection_execution' and r['dp']==actor]
    observations=[]
    for i,entry in enumerate(events):
        if entry['address']!='80E48D':continue
        if i+1>=len(events) or events[i+1]['address']!='80E49A':
            raise ValueError('Missing immediate matching return event')
        observations.append(evaluate(entry,events[i+1],table))
    if not observations:raise ValueError('No field-write observations for initial P2 actor')
    return {'observations':observations,'limitations':['Only the observed 80:E48D path is modeled; other writers of +$86 exist.',
            'The semantic meaning and all writers of input A and +$84 are not established here.',
            'These captures do not identify the sporting name or fully reproduce the action.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rom=a.rom.read_bytes();raw=a.trace.read_bytes();table=read_table(rom)
    result=analyze([json.loads(l) for l in raw.splitlines() if l.strip()],table)
    result.update({'schema':'issd-field86-observation/v1','rom_table':table,
                   'source':{'trace':a.trace.as_posix(),'trace_sha256':hashlib.sha256(raw).hexdigest(),
                             'rom_sha256':hashlib.sha256(rom).hexdigest()},
                   'rom_offsets':{'routine':'0x648D','table':'0x96B2','header_adjusted':len(rom)%0x8000}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('observations:',len(result['observations']),'matched:',sum(x['matches_rom_formula'] for x in result['observations']))


if __name__=='__main__':main()
