"""Audit the observed goalkeeper B-release event against a neutral replay."""
import argparse,hashlib,json
from pathlib import Path
from audit_issd_goalkeeper_input_trials import audit as audit_inputs

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return [json.loads(s) for s in path.read_text(encoding='utf8').splitlines() if s.strip()]
def s16(n):return n if n<32768 else n-65536

def audit(action,neutral,state):
    inputs=audit_inputs(neutral/'trial.jsonl',[action/'trial.jsonl'],state)
    a=inputs['trials'][0]
    if (a['button'],a['start'],a['first_observed_difference'])!=('B',20,21):raise ValueError('Unexpected paired trial')
    events=rows(action/'keeper-transfers.jsonl');other=rows(neutral/'keeper-transfers.jsonl')
    if not any(x.get('type')=='session_end' for x in events) or not any(x.get('type')=='session_end' for x in other):raise ValueError('Incomplete hook trace')
    hooks=[x for x in events if x.get('type')=='release_hook' and x['address']=='85EE38']
    if len(hooks)!=1:raise ValueError('Expected one high-throw dispatch')
    h=hooks[0]
    if (h['frame'],h['actor'],h['script'],h['link_a6'],h['timer70'])!=(4472,0x500,0xe644,0x500,0):raise ValueError('Unexpected dispatch context')
    if any(x.get('type')=='release_hook' and x['address']=='85EE38' for x in other):raise ValueError('Control executed dispatch')
    generic=[x for x in events if x.get('type')=='release_hook' and x['address']=='85F8B9' and x['frame']==h['frame']]
    if len(generic)!=1 or generic[0]['actor']!=h['actor']:raise ValueError('Expected linked generic release dispatch')
    action_rows={x['frame']:x for x in rows(action/'trial.jsonl') if 'step' in x}
    neutral_rows={x['frame']:x for x in rows(neutral/'trial.jsonl') if 'step' in x}
    before=action_rows[4472];after=action_rows[4473];control=neutral_rows[4473]
    if before['link_a6']!=0x500 or after['link_a6']!=0 or control['link_a6']!=0x500:raise ValueError('Unexpected link transition')
    if tuple(s16(after[k]) for k in ('ball_vx','ball_vy','ball_vz'))!=(4,0,-3):raise ValueError('Unexpected observed ball velocity')
    if any(s16(control[k])!=0 for k in ('ball_vx','ball_vy','ball_vz')):raise ValueError('Unexpected neutral velocity')
    def state_row(row):
        keys=('frame','step','state','script','descriptor','link_a6','ball_x','ball_y','ball_z','ball_vx','ball_vy','ball_vz')
        return {k:(s16(row[k]) if k.startswith('ball_') else row[k]) for k in keys}
    return {'schema':'issd-goalkeeper-throw-release-audit/v1','state_sha256':digest(state),
       'action_trial_sha256':digest(action/'trial.jsonl'),'neutral_trial_sha256':digest(neutral/'trial.jsonl'),
       'action_hooks_sha256':digest(action/'keeper-transfers.jsonl'),'neutral_hooks_sha256':digest(neutral/'keeper-transfers.jsonl'),
       'pre_input_samples_match':a['pre_input_samples_match'],'first_difference_step':a['first_observed_difference'],
       'hook_entry':h,'before':state_row(before),'after':state_row(after),'neutral_at_after':state_row(control),
       'limitations':['Hook records entry before execution, not the completed routine.',
          'Results describe one state, goalkeeper, direction and input window.',
          'Ball values are raw signed words, not calibrated physical units.',
          'The link and velocity transition is observed; it does not establish all ownership or collision rules.',
          'No general animation/ball synchronization or other direction is inferred.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',type=Path);p.add_argument('neutral',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();r=audit(a.action,a.neutral,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: paired goalkeeper release observed')
if __name__=='__main__':main()
