"""Audit eight held-direction action replays against a common neutral replay."""
import argparse
import hashlib
import json
from pathlib import Path

from analyze_issd_action_selector import analyze as selection,rom_tables
from analyze_issd_field86 import analyze as field86,read_table
from analyze_issd_input_origin import analyze as origin,read_rom
from compare_issd_action_trials import compare,load

NIBBLES={'Right':1,'Left':2,'Down':4,'DownRight':5,'DownLeft':6,
         'Up':8,'UpRight':9,'UpLeft':10}


def audit_trial(name,rows,action,neutral,angle_table,dpad_table,field_table,control_table,script_table):
    baseline=compare(action,neutral,0x40)
    source=origin(rows,angle_table,dpad_table)['observations']
    writes=field86(rows,field_table)['observations']
    try:
        selectors=selection(rows,control_table,script_table)['observations']
    except ValueError as exc:
        if str(exc)!='No matching selection sequence for the controlled actor':raise
        selectors=[]
    if len(source)!=1 or len(writes)!=1 or len(selectors)>1:raise ValueError('Expected at most one observed path per replay')
    i,f=source[0],writes[0]
    s=selectors[0] if selectors else None
    field_matched=(baseline['baseline_matches_observed_fields'] and baseline['p2_action_input_confirmed']
             and baseline['p2_control_neutral_in_action_window'] and i['path']=='held_direction_lookup'
             and i['dpad_nibble']==NIBBLES[name] and i['controller_held']==((NIBBLES[name]<<8)|0x40)
             and i['matches_lookup'] and f['matches_rom_formula']
             and i['step']==f['step'] and i['actor']==f['actor'])
    matched=bool(field_matched and s and s['matches_rom_table'] and
                 i['step']==s['step'] and i['actor']==s['actor'])
    alt_events=[r for r in rows if r.get('type')=='selection_execution' and r['dp']==i['actor'] and r['step']==i['step']]
    alt_entry=next((r for r in alt_events if r['address']=='8496B8'),None)
    alt_dispatch=next((r for r in alt_events if r['address']=='84E6AC'),None)
    alt_hooks={r.get('address') for r in rows if r.get('type')=='selection_hook_registration' and r.get('success')}
    alt_confirmed=bool(field_matched and not s and f['field_86_after']&0x8000 and alt_entry and alt_dispatch and
                       {'8496B8','84E6AC'}<=alt_hooks and alt_events.index(alt_entry)<alt_events.index(alt_dispatch) and
                       alt_dispatch['a']==0xD280 and alt_dispatch['y']==0xE4EA)
    return {'direction':name,'baseline_samples':baseline['before_compared'],
            'baseline_matches_observed_fields':baseline['baseline_matches_observed_fields'],
            'control_neutral':baseline['p2_control_neutral_in_action_window'],
            'button_confirmed':baseline['p2_action_input_confirmed'],'held':i['controller_held'],
            'dpad_nibble':i['dpad_nibble'],'lookup_output':i['output_a'],
            'actor_direction':f['direction'],'field_86':f['field_86_after'],
            'field_checks_pass':field_matched,
            'selector_status':'observed' if s else 'not_observed',
            'control':s['control'] if s else None,'script':s['script'] if s else None,
            'alternate_route_observed':alt_confirmed,
            'alternate_script':alt_dispatch['a'] if alt_confirmed else None,
            'matched_all_checks':matched,
            'source':{k:v for k,v in action.items() if k!='samples'}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('neutral',type=Path)
    p.add_argument('--trial',action='append',nargs=2,metavar=('DIRECTION','TRACE'),required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    trials=dict(a.trial)
    if len(trials)!=len(a.trial) or set(trials)!=set(NIBBLES):p.error('provide each of the eight directions exactly once')
    rom=a.rom.read_bytes();angle,dpad=read_rom(rom);fields=read_table(rom);controls,scripts=rom_tables(rom);neutral=load(a.neutral)
    results=[]
    for name,path in trials.items():
        trace=Path(path); raw=trace.read_bytes();rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        results.append(audit_trial(name,rows,load(trace),neutral,angle,dpad,fields,controls,scripts))
    result={'schema':'issd-held-directions-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'neutral_source':{k:v for k,v in neutral.items() if k!='samples'},'trials':results,
            'limitations':['Same-field pre-action comparisons do not establish equality of all emulator state.',
                           'These trials exercise one savestate, actor, preparation and control configuration.',
                           'No conclusion is made about other action branches, sporting meaning or full web integration.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('modeled selector:',sum(r['matched_all_checks'] for r in results),
          'alternate observed:',sum(r['alternate_route_observed'] for r in results),'/',len(results))


if __name__=='__main__':main()
