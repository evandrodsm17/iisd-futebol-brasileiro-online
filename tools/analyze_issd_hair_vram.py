"""Audit auxiliary hair tile uploads against the local ROM and runtime trace."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import lorom_offset


def analyze(rom,rows):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    rom=rom[header:]
    if not any(x.get('type')=='hook' and x.get('success') for x in rows):raise ValueError('Missing hook')
    if not any(x.get('type')=='session_end' and x.get('steps')==120 for x in rows):raise ValueError('Incomplete capture')
    frames=[r for r in rows if r.get('type')=='vram'];index={(r['context'],r['step']):r for r in frames}
    if len(index)!=len(frames) or not frames:raise ValueError('Duplicate or missing VRAM observations')
    counts=Counter(); contexts=Counter(); observations=[]
    for row in frames:
        offset=row['hair_offset'];desc=row['descriptor'];slot=row['slot']
        if offset%4 or not 0<=offset<=48 or not 0x8000<=desc<=0xffff or not 0<=slot<0x200:
            raise ValueError('Invalid context selector')
        if row['vram_offset']!=(0xc000+slot*32)%0x10000:raise ValueError('Unexpected VRAM address')
        descriptor_offset=0x10000+(desc&0x7fff);selector=rom[descriptor_offset+8]
        if not 1<=selector<=24:raise ValueError('Invalid atlas selector')
        address=int.from_bytes(rom[0xed6d+offset:0xed70+offset],'little')
        source=lorom_offset(address)+(selector-1)*32
        expected=rom[source:source+32].hex()
        if len(expected)!=64 or len(row['bytes'])!=64:raise ValueError('Incomplete tile')
        same=row['bytes']==expected;counts['same_step_match' if same else 'same_step_mismatch']+=1
        after=index.get((row['context'],row['step']+1))
        if after and after['descriptor']==desc:
            if after['bytes']!=expected:raise ValueError('Stable next frame does not match ROM')
            counts['next_frame_stable_match']+=1
        contexts[(row['context'],row['parent'],offset//4+1)]+=1
        if not same:
            previous=index.get((row['context'],row['step']-1))
            if previous and previous['descriptor']==desc:raise ValueError('Mismatch without descriptor transition')
        observations.append({'step':row['step'],'context':row['context'],'parent':row['parent'],
                             'descriptor':desc,'atlas_style':offset//4+1,'selector':selector,
                             'vram_offset':row['vram_offset'],'same_step_match':same})
    if not counts['same_step_match'] or not counts['next_frame_stable_match']:
        raise ValueError('No verifiable matches')
    return {'schema':'issd-hair-vram-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'counts':dict(counts),'contexts':[{'context':c,'parent':p,'atlas_style':s,'samples':n} for (c,p,s),n in contexts.items()],
            'observations':observations,
            'limitations':['VRAM tile equality alone does not prove OAM placement, palette, occlusion or full actor association.',
                           'Only contexts and styles observed in this replay are covered.',
                           'A same-step mismatch can reflect transfer timing; no universal frame offset is inferred.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();raw=a.trace.read_bytes()
    result=analyze(a.rom.read_bytes(),[json.loads(l) for l in raw.splitlines() if l.strip()])
    result['source']={'path':a.trace.as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('Audit:',result['counts'])
