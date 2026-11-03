"""Compare consecutive free-ball integration entries with 16.16 addition."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def u32(high, low):
    return (high << 16) | low


def signed32(value):
    value &= 0xffffffff
    return value - 0x100000000 if value & 0x80000000 else value


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    code = bytes.fromhex('18b50675229506b508752495088dc81b18b50a7526950ab50c7528950c95128dcc1b60')
    if header not in (0, 512) or rom[header+0x189fb:header+0x189fb+len(code)] != code:
        raise ValueError('Unexpected ball integration instructions')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay comparison failed')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    if not {'8389FB','8390E6'} <= {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}:
        raise ValueError('Missing hooks')
    entries = {}
    for r in rows:
        if r.get('type') == 'ball_update_execution' and r.get('address') == '8389FB' and 493 <= r['step']-action['trigger'] <= 501:
            t = r['step']-action['trigger']
            if t in entries: raise ValueError('Ambiguous integration callback')
            entries[t] = r
    if set(entries) != set(range(493,502)):
        raise ValueError('Missing consecutive integration entries')
    steps=[]
    for t in range(493,501):
        a,b=entries[t],entries[t+1]
        if a['ball_type'] != 1 or b['ball_type'] != 1:
            raise ValueError('Different ball type')
        axes={}
        for key,pos,frac,vel,vfrac in (('x','x_pos','x_fraction','vx','vx_fraction'),('y','y_pos','y_fraction','vy','vy_fraction')):
            before=u32(a[pos],a[frac]);velocity=u32(a[vel],a[vfrac]);after=u32(b[pos],b[frac])
            predicted=(before+velocity)&0xffffffff
            axes[key]={'before':before,'velocity':velocity,'predicted':predicted,'observed_next':after,
                       'difference_signed_16_16':signed32(after-predicted)}
        if axes['x']['difference_signed_16_16'] != -3*65536 or axes['y']['difference_signed_16_16'] != 0:
            raise ValueError('Observed position correction differs')
        steps.append({'elapsed':t,'next_elapsed':t+1,'axes':axes})
    return {'schema':'issd-ball-step-motion/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'sources':[{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace,neutral)],
            'baseline_samples':proof['before_compared'],'integration_lorom_offset':'0x189FB', 'steps':steps,
            'limitations':['Entry-to-entry difference includes all other code executed between callbacks.',
                           'The source and meaning of the X correction are not established.',
                           'One scenario does not define general ball physics.']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('trace',type=Path);p.add_argument('neutral',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=analyze(a.rom.read_bytes(),a.trace,a.neutral)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Validated {len(result['steps'])} consecutive integration intervals")
