"""Audit accelerated open-match period routes and locally captured screens."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(raw):return hashlib.sha256(raw).hexdigest()


def audit(rom_path,root):
    rom=rom_path.read_bytes()
    expected=bytes.fromhex('22 07 d4 86 22 31 92 a4 22 53 92 a4 22 6d c6 83 e6 a8')
    if rom[0x125898:0x125898+len(expected)]!=expected:raise ValueError('Unexpected phase handler')
    cases=[]
    for name,score_mode,forced_phases in [('draw','draw',[0,1,2,3]),('home','home',[0,1]),('draw-override0','draw',[0,1,2,3])]:
        directory=root/f'open-period-v3-{name}'
        raw=(directory/'trace.jsonl').read_bytes()
        rows=[json.loads(line) for line in raw.splitlines()]
        start,end=rows[0],rows[-1]
        if start.get('type')!='session_start' or not start.get('synthetic_clock') or start.get('score_mode')!=score_mode or start.get('game_time')!=1 or start.get('initial_overtime')!=1 or end!={'type':'session_end','steps':8000}:
            raise ValueError(f'Unexpected capture configuration: {name}')
        scores=[e for e in rows if e['type']=='score_intervention']
        if score_mode=='home':
            if scores!=[{'type':'score_intervention','side':'home','before':0,'after':1}]:raise ValueError('Unexpected score change')
        elif scores:raise ValueError('Unexpected score change in draw')
        overrides=[e for e in rows if e['type']=='overtime_intervention']
        if name=='draw-override0':
            if overrides!=[{'type':'overtime_intervention','before':1,'after':0}]:raise ValueError('Unexpected setting change')
        elif overrides:raise ValueError('Unexpected setting intervention')
        clock_writes=[e for e in rows if e['type']=='clock_intervention']
        if [e['phase'] for e in clock_writes]!=forced_phases or any(e['after']!=1 for e in clock_writes):raise ValueError('Unexpected clock interventions')
        expected_dispatch=forced_phases[:-1]
        hooks=[e for e in rows if e['type']=='hook' and e['site']=='A4D8A8']
        if [e['phase'] for e in hooks]!=expected_dispatch or any(e['d']!=0 for e in hooks):raise ValueError('Unexpected phase handler')
        starts=[]
        for phase in forced_phases:
            candidates=[e for e in rows if e['type']=='frame' and e['mode']==6 and e['scene']==8 and e['state']==0 and e['phase']==phase]
            if not candidates:raise ValueError('Missing active period')
            e=min(candidates,key=lambda r:r['step'])
            if e['carrierTeam']!=[0xe00,0xd00,0xe00,0xd00][phase]:raise ValueError('Unexpected kickoff team')
            if e['overtime']!=(0 if name=='draw-override0' else 1):raise ValueError('Unexpected active overtime setting')
            if phase>0 and e['clock']!=[None,0x500,0x300,0x300][phase]:raise ValueError('Unexpected initial timer')
            starts.append({k:e[k] for k in ('step','phase','clock','carrier','carrierTeam','team0Flags','team1Flags','home','away','overtime')})
        images=[]
        requested=[(0,18),(0,12),(1,18),(1,12)]
        if score_mode=='draw':requested.append((3,12))
        for phase,scene in requested:
            captures=[e for e in rows if e['type']=='screenshot' and e['phase']==phase and e['scene']==scene and e['success']]
            if not captures:raise ValueError('Missing screenshot')
            capture=max(captures,key=lambda e:e['step'])
            data=(directory/capture['file']).read_bytes()
            if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid screenshot')
            images.append({'phase':phase,'scene':scene,'step':capture['step'],'sha256':digest(data)})
        cases.append({'name':name,'trace_sha256':digest(raw),'initial':start,'score_interventions':scores,
                      'overtime_interventions':overrides,'clock_interventions':clock_writes,'active_periods':starts,
                      'phase_handler_calls':hooks,'screenshot_hashes':images,
                      'menu_pulse_count':sum(e['type']=='menu_pulse' for e in rows)})
    return {'schema':'issd-open-match-periods/v1','cases':cases,
            'visual_review':['Phase 0 scene 18 shows match statistics; scene 12 shows the team setup menu.',
                             'The decisive phase 1 scene 12 shows the main game-mode menu.',
                             'The tied phase 3 scene 12 shows the player order selection for penalties.'],
            'limits':['All clocks were accelerated by explicit RAM writes; the home-leading score was also written synthetically.',
                      'The overtime-setting override is synthetic and this one game mode showed the same phase route; its general meaning remains unproven.',
                      'Automatic A pulses navigate non-play scenes and may skip interactions.',
                      'One saved game, game-time setting and match setup; exact rules and timing may vary.',
                      'Screens are visually reviewed, not automatically recognized; raw images, ROM and saved state stay local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','root','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=audit(args.rom,args.root)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK: three accelerated open-match period routes audited')
