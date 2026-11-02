"""Compare two independently started trials, proving baseline equality before interpretation."""
import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    raw=path.read_bytes();rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    starts=[r for r in rows if r.get('type')=='experiment_start']
    if len(starts)!=1:raise ValueError('Expected exactly one experiment trigger')
    trigger=starts[0]['step']
    samples={r['step']-trigger:r for r in rows if 'step' in r and not r.get('type')}
    return {'samples':samples,'trigger':trigger,'sha256':hashlib.sha256(raw).hexdigest(),
            'bytes':len(raw),'path':path.as_posix()}


def signature(row):
    actors=tuple((a['address'],a['type'],a['state'],a['direction'],a['x'],a['x_fraction'],
                  a['y'],a['y_fraction'],a['team']) for a in row.get('actors',[]))
    controls=tuple((c['address'],c['actor'],c['flags'],c['held']) for c in row.get('controls',[]))
    return (row['mode1'],row['mode2'],row['phase'],row['player_setting'],row['selected_p1'],
            row['link_a4'],row['link_a6'],tuple(row['ball'][k] for k in ('x','y','z')),actors,controls)


def compare(a,b):
    common=sorted(set(a['samples']) & set(b['samples']))
    before=[t for t in common if 0<=t<480]
    after=[t for t in common if 480<=t<600]
    mismatches=[t for t in before if signature(a['samples'][t])!=signature(b['samples'][t])]
    ball_diffs=[t for t in after if tuple(a['samples'][t]['ball'][k] for k in ('x','y','z'))!=
                tuple(b['samples'][t]['ball'][k] for k in ('x','y','z'))]
    input_checks=[t for t in common if 480<=t<486]
    action_confirmed=sum(1 for t in input_checks if a['samples'][t].get('held_p2',0)&0x80
                         and not (b['samples'][t].get('held_p2',0)&0x80))
    return {'before_compared':len(before),'before_mismatch_count':len(mismatches),
            'first_before_mismatch':mismatches[0] if mismatches else None,
            'after_compared':len(after),'after_ball_difference_count':len(ball_diffs),
            'first_after_ball_difference':ball_diffs[0] if ball_diffs else None,
            'baseline_matches_observed_fields':len(before)==240 and not mismatches,
            'p2_action_samples_compared':len(input_checks),
            'p2_action_held_only_in_action_trial':action_confirmed,
            'p2_action_input_confirmed':len(input_checks)==3 and action_confirmed==3,
            'limitations':['Separate boots are not proof of identical hidden state.',
              'Only explicitly logged fields were compared; sampling skips alternate frames.',
              'Ball differences do not alone identify a pass or shot.',
              'A missing or mismatched baseline prevents causal attribution.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    a,b=load(args.action),load(args.control);result=compare(a,b)
    result.update({'schema':'issd-action-trial-comparison/v1',
                   'sources':[{k:v for k,v in x.items() if k!='samples'} for x in (a,b)]})
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','limitations')},indent=2))
