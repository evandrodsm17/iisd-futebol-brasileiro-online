"""Audit opponent reaction in paired passive defensive replays."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issd_defense_approach import pair
from extract_issd_catalog import EXPECTED_MD5
from resolve_issd_animation_assets import asset_ranges, read_descriptor


def read(path):
    raw=path.read_bytes()
    return [json.loads(line) for line in raw.splitlines() if line.strip()],hashlib.sha256(raw).hexdigest()


def segments(rows):
    out=[]
    for r in rows:
        actor=r['opponent'];item={'frame':r['frame'],'state':actor['state'],'script':actor['script'],
                                  'descriptor':actor['descriptor'],'phase':r['phase'],'link_a6':r['link_a6']}
        if out and all(out[-1][k]==item[k] for k in ('state','script','descriptor','phase','link_a6')):
            out[-1]['last_frame']=item['frame'];out[-1]['frames']+=1
        else:item.update(last_frame=item['frame'],frames=1);out.append(item)
    return out


def audit(root,rom_path,state_path,pointers,end_frame=4380):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    comparison=pair(root/'A',root/'NEUTRAL','Right');actor=comparison['selected_actor_at_action']
    a,ah=read(root/'A'/'defense-opponent.jsonl');n,nh=read(root/'NEUTRAL'/'defense-opponent.jsonl')
    first=comparison['first_input_frame']
    af={r['frame']:r for r in a if r['type']=='frame_end'};nf={r['frame']:r for r in n if r['type']=='frame_end'}
    if not 4380<=end_frame<=5000:raise ValueError('Invalid end frame')
    expected=set(range(4274,end_frame+1))
    if set(af)!=expected or set(nf)!=expected:raise ValueError('Missing paired frame samples')
    for f in range(4274,first):
        for key in ('player','opponent','ball','link_a6','phase','foul_setting','global_11fa'):
            if af[f][key]!=nf[f][key]:raise ValueError(f'Extra-field baseline mismatch {f}/{key}')
    hooks=[r for r in a if r['type']=='execution'];neutral_hooks=[r for r in n if r['type']=='execution']
    required=['opponent_entry','before_write_78','after_write_78','after_link',
              'response_dispatch','response_case_2','foul_gate_entry','response_init_0328']
    if [r['site'] for r in hooks[:len(required)]]!=required:raise ValueError('Unexpected response route')
    if neutral_hooks:raise ValueError('Control unexpectedly reached response hooks')
    before,hwrite,after,linked=hooks[:4]
    if not (before['opponent']['f76']!=actor and hwrite['opponent']['f76']==actor and
            hwrite['opponent']['f78']==before['opponent']['f78'] and after['opponent']['f78']==2 and
            before['link_a6']==0x1900 and linked['link_a6']==actor):raise ValueError('Unexpected contact transition')
    if not (len(comparison['gate_events'])==1 and comparison['gate_events'][0]['carry']==0):raise ValueError('No accepted contact')
    action_segments=segments([af[f] for f in sorted(af)])
    reference_segments=segments([nf[f] for f in sorted(nf)])
    expected_states=[0x00b8,0x0328,0x0330,0x0360,0x0350]
    if end_frame>=4484:expected_states += [0x02f8,0x0010]
    distinct=list(dict.fromkeys(r['state'] for r in action_segments))
    if distinct!=expected_states:raise ValueError(f'Unexpected states: {distinct}')
    if end_frame>=4484:
        sequence=[r['site'] for r in hooks]
        key_events=['response_0350_animation_done','response_leave_0350','recovery_init','return_no_ball']
        positions=[next((i for i,s in enumerate(sequence) if s==key),None) for key in key_events]
        if any(i is None for i in positions) or positions!=sorted(positions):raise ValueError('Incomplete recovery hook chain')
    ranges=asset_ranges(pointers);assets=[]
    for desc in (0xb5a1,0xb5aa,0xb4f6):
        entry=read_descriptor(rom,desc);source=entry['graphics_source']
        assets.append({'descriptor':desc,'graphics_source':source,
                       'asset':next((name for lo,hi,name in ranges if lo<=source<=hi),None)})
    return {'schema':'issd-defense-opponent/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'declared_state_sha256':hashlib.sha256(state_path.read_bytes()).hexdigest(),
            'asset_pointers_sha256':hashlib.sha256(pointers.read_bytes()).hexdigest(),
            'baseline_samples':comparison['baseline_samples'],'action_trace_sha256':comparison['action_trace_sha256'],
            'neutral_trace_sha256':comparison['neutral_trace_sha256'],'action_probe_sha256':ah,'neutral_probe_sha256':nh,
            'actor':actor,'previous_carrier':0x1900,'contact_events':hooks[:len(required)],
            'observation_end_frame':end_frame,
            'subsequent_hook_sites':sorted(set(r['site'] for r in hooks[len(required):])),
            'action_segments':action_segments,'neutral_segments':reference_segments,'asset_labels':assets,
            'limitations':['One context under script DF7F, not an accepted DB25 slide contact.',
                           'Phase remained observed at zero; this alone does not prove foul rules or settings.',
                           'Asset labels do not validate animation composition or causal semantics.',
                           'Control comparisons cover logged fields, not all emulator state.',
                           'The declared state identity is not authenticated by the trace.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True)
    p.add_argument('--pointers',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--end-frame',type=int,default=4380)
    a=p.parse_args();r=audit(a.root,a.rom,a.state,a.pointers,a.end_frame);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('audited reaction segments:',len(r['action_segments']))
