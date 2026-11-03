"""Audit one paired passive trace of the native contact and link update."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issd_defense_approach import pair


def read_events(path):
    raw = path.read_bytes()
    return [json.loads(line) for line in raw.splitlines() if line.strip()], hashlib.sha256(raw).hexdigest()


def audit(root, state):
    action, neutral = root/'A', root/'NEUTRAL'
    comparison = pair(action, neutral, 'Right')
    events, action_hash = read_events(action/'defense-link.jsonl')
    control, control_hash = read_events(neutral/'defense-link.jsonl')
    start = comparison['first_input_frame']
    actor = comparison['selected_actor_at_action']
    if [e for e in events if e['frame'] < start] != [e for e in control if e['frame'] < start]:
        raise ValueError('Instruction trace baseline differs')
    window = [e for e in events if start <= e['frame'] <= start+20 and e['actor'] == actor]
    control_window = [e for e in control if start <= e['frame'] <= start+20 and e['actor'] == actor]
    names = [e['site'] for e in window]
    required = ['contact_entry','contact_result','opponent_response','link_path','prepare_link',
                'reset_link_context','clear_link','after_clear_link','store_link','after_link']
    if names != required or control_window:
        raise ValueError(f'Unexpected instruction trace: {names}')
    indexed = {e['site']:e for e in window}
    old = indexed['contact_entry']['link_a6']
    if not (old and old != actor and indexed['clear_link']['link_a6'] == old and
            indexed['after_clear_link']['link_a6'] == 0 and
            indexed['store_link']['x'] == actor and indexed['store_link']['link_a6'] == 0 and
            indexed['after_link']['link_a6'] == actor and
            indexed['contact_result']['f6e'] & 0x400):
        raise ValueError('Link transition or accepted flag did not match')
    if len(comparison['gate_events']) != 1 or comparison['gate_events'][0]['carry'] != 0:
        raise ValueError('Expected one naturally accepted gate')
    return {'schema':'issd-defense-link-probe/v1',
            'declared_state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
            'comparison':comparison, 'instruction_events':window,
            'instruction_sha256':action_hash, 'control_instruction_sha256':control_hash,
            'limitations':['Only logged baseline fields are compared.',
                           'The instruction probes apply to one scenario, not all defensive actions.',
                           'The input state is declared by the operator, not authenticated by the trace.',
                           'Contact with the DB25 script remains unverified.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.output.write_text(json.dumps(audit(args.root,args.state),indent=2)+'\n',encoding='utf-8')
    print('audited native link transition')
