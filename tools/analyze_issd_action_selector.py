"""Verify observed action-script selection against the local ROM tables."""
import argparse
import hashlib
import json
from pathlib import Path


def rom_tables(rom):
    header=len(rom)%0x8000
    if header not in (0,512):raise ValueError('Unsupported ROM header')
    def values(offset):
        raw=rom[header+offset:header+offset+8]
        if len(raw)!=8:raise ValueError('ROM truncated')
        return [int.from_bytes(raw[i:i+2],'little') for i in range(0,8,2)]
    return values(0xc510),values(0xc520)


def analyze(rows, control_table, script_table):
    registrations=[r for r in rows if r.get('type')=='selection_hook_registration']
    events=[r for r in rows if r.get('type')=='selection_execution']
    starts=[r for r in rows if r.get('type')=='experiment_start']
    if len(starts)!=1 or not any(r.get('type')=='session_end' and r.get('reason')=='experiment_window_complete' for r in rows):
        raise ValueError('Incomplete or ambiguous replay')
    if len(registrations)!=4 or not all(r.get('success') for r in registrations):
        raise ValueError('Selection hooks not fully registered')
    target=starts[0]['p2']; observations=[]
    for i,event in enumerate(events):
        if event['address']!='84E600':continue
        preceding=[r for r in events[:i] if r['step']==event['step'] and r['dp']==target]
        if not any(r['address']=='84968B' for r in preceding) or not any(r['address']=='80E4C7' for r in preceding):continue
        index=(event['field_86']>>8)&7
        if index not in (0,2,4,6):raise ValueError('Unsupported odd table byte offset')
        observed=(event['x'],event['a'],event['y'])
        expected=(index,control_table[index//2],script_table[index//2])
        observations.append({'step':event['step'],'frame':event['frame'],'actor':target,
                             'field_86':event['field_86'],'direction':event['direction'],
                             'table_byte_offset':index,'control':event['a'],'script':event['y'],
                             'matches_rom_table':observed==expected})
    if not observations:raise ValueError('No matching selection sequence for the controlled actor')
    return {'observations':observations,'limitations':['Observed field values and paths apply only to this replay and actor.',
            'The semantic meaning and writers of actor field +$86 are not established here.',
            'This selection does not by itself identify pass, shot, or final animation appearance.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rom=a.rom.read_bytes();raw=a.trace.read_bytes();control,scripts=rom_tables(rom)
    result=analyze([json.loads(l) for l in raw.splitlines() if l.strip()],control,scripts)
    result.update({'schema':'issd-action-selector-observation/v1',
                   'source':{'trace':a.trace.as_posix(),'trace_sha256':hashlib.sha256(raw).hexdigest(),
                             'rom_sha256':hashlib.sha256(rom).hexdigest()},
                   'rom_offsets':{'control_table':'0xC510','script_table':'0xC520','header_adjusted':len(rom)%0x8000}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('observations:',len(result['observations']),'matched:',sum(o['matches_rom_table'] for o in result['observations']))


if __name__=='__main__':main()
