"""Audit reaction-choice inputs for the paired slide-contact/fall replay."""
import argparse, hashlib, json
from pathlib import Path
from compare_issd_action_trials import signature, has_extended
from audit_issd_slide_reaction_choice import one_trace, sha
from extract_issd_catalog import EXPECTED_MD5

def audit(action_dir,neutral_dir,rom_path,state_path):
    action,neutral=one_trace(action_dir),one_trace(neutral_dir)
    a,n=action['samples'],neutral['samples']
    before=sorted(t for t in set(a)&set(n) if 0<=t<480)
    if not any(set(range(i,480,2))<=set(before) for i in (0,1)): raise ValueError('Incomplete baseline')
    if any(not has_extended(a[t]) or not has_extended(n[t]) or signature(a[t],True)!=signature(n[t],True) for t in before): raise ValueError('Baseline mismatch')
    if any(a[t]['held_p1']!=0x180 or n[t]['held_p1']!=0x100 or a[t]['held_p2']!=0 or n[t]['held_p2']!=0 for t in range(480,486)): raise ValueError('Unexpected inputs')
    path=action_dir/'slide-reaction-choice.jsonl'
    rows=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]
    if [r['site'] for r in rows]!=['choice_entry','record_return','dispatch'] or len({r['frame'] for r in rows})!=1: raise ValueError('Unexpected event sequence')
    entry,record,dispatch=rows
    if entry['d']!=0xd00 or entry['x']!=0x1900 or record['d']!=0x1900 or dispatch['target78']!=0x2002 or dispatch['target76']!=0xd00 or dispatch['ball_owner']!=0x1900: raise ValueError('Unexpected reaction')
    if record['a']!=record['record_word']: raise ValueError('Roster pointer or returned word mismatch')
    classes=(0,0,0,1,1,2);slot=entry['attacker30']&255
    if slot<1 or slot>len(classes): raise ValueError('Unknown attacker class')
    ability=(record['record_word']>>4)&15;other=(record['record_next_word']>>4)&15;detail=record['record_sixth_word']&15
    index=((ability+other)//2+detail+classes[slot-1])*4+(entry['global78']&3)
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5 or index>=68: raise ValueError('Unexpected ROM or table index')
    value=rom[0x957f+index]
    if value!=0: raise ValueError('Unexpected table result')
    if a[484]['link_a6']!=0x1900 or a[485]['link_a6']!=0 or n[485]['link_a6']!=0x1900: raise ValueError('Unexpected possession transition')
    return {'schema':'issd-slide-reaction-fall-observation/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'state_sha256':sha(state_path),'action_trace_sha256':action['sha256'],'neutral_trace_sha256':neutral['sha256'],'hooks_sha256':sha(path),'baseline_samples':len(before),'frame':entry['frame'],'entry':entry,'record':record,'dispatch':dispatch,'index':index,'table_byte':value,'limitations':['One replay and one paired neutral control; logged baseline fields are not the full machine state.','The table byte is read from the ROM using captured inputs, not directly observed at its load instruction.','Foul setting was not captured; this event bypasses the early foul condition because target68 is nonzero.','Global 78 differs between cases; its semantic meaning and how to reproduce it on the web remain unproven.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',type=Path);p.add_argument('neutral',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=audit(args.action,args.neutral,args.rom,args.state)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('OK: reação de queda; índice',result['index'],'e byte',result['table_byte'])
