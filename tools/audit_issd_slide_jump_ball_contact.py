"""Correlate natural slide ball-gate and jump observations in a paired replay."""
import argparse
import hashlib
import json
from pathlib import Path

from compare_issd_action_trials import has_extended, load, signature


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]


def audit(root):
    action, neutral = root / 'A', root / 'NEUTRAL'
    def trace(directory):
        files = list(directory.glob('issd-auto-probe-*.jsonl'))
        if len(files) != 1:
            raise ValueError('Expected one replay trace per trial')
        return load(files[0])
    a, n = trace(action), trace(neutral)
    before = sorted(t for t in set(a['samples']) & set(n['samples']) if 0 <= t < 420)
    if len(before) != 215 or any(not has_extended(a['samples'][t]) or not has_extended(n['samples'][t]) or signature(a['samples'][t], True) != signature(n['samples'][t], True) for t in before):
        raise ValueError('Paired baseline does not match')
    for t in range(420, 426):
        if a['samples'][t]['held_p1'] != 0x80 or n['samples'][t]['held_p1'] != 0:
            raise ValueError('Unexpected action input')
    gates = read(action / 'slide-ball-gate.jsonl')
    accepted = [r for r in gates if r['frame'] == 4221 and r['script'] == 0xdb25 and r['carry'] == 0 and r['synthetic'] is False]
    if len(accepted) != 1:
        raise ValueError('Expected one accepted natural ball gate')
    gate = accepted[0]
    if gate['actor'] != 0xd00 or gate['flags_after'] & 0x400 == 0:
        raise ValueError('Unexpected gate actor or result flag')
    hooks = read(action / 'slide-contact-route.jsonl')
    jump = [r for r in hooks if r['frame'] == 4221 and r['site'] == 'jump_entry']
    if len(jump) != 1 or jump[0]['actor'] != 0x1900 or jump[0]['link_a6'] != 0x1900 or jump[0]['actor_reaction'] & 15 != 4:
        raise ValueError('Unexpected carrier reaction')
    for t in range(420, 461):
        if a['samples'][t]['link_a6'] != 0x1900 or n['samples'][t]['link_a6'] != 0x1900:
            raise ValueError('Carrier link not preserved throughout paired window')
    return {'schema': 'issd-slide-jump-ball-contact/v1', 'action_trace_sha256': a['sha256'],
            'neutral_trace_sha256': n['sha256'], 'gate_sha256': sha(action / 'slide-ball-gate.jsonl'),
            'hooks_sha256': sha(action / 'slide-contact-route.jsonl'), 'baseline_samples': len(before),
            'frame': 4221, 'ball_gate': gate,
            'reaction': {'site': jump[0]['site'], 'actor': jump[0]['actor'], 'reaction': jump[0]['actor_reaction'], 'ball_link': jump[0]['link_a6']},
            'carrier_link_preserved_elapsed_steps': [420, 460],
            'limits': ['One paired replay and geometry; matched logged fields are not complete machine state.',
                       'Gate and jump occur in the same frame; separate hooks do not prove their instruction order or causality.',
                       'An accepted gate is not by itself proof of an actual kick or touch of the ball.',
                       'Other directions, skills, rules and whether the jump is automatic remain unproven.',
                       'Native-to-browser coordinate mapping and gameplay effects are not established.',
                       'ROM, state, screenshots and raw traces remain local.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = audit(args.root)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: accepted gate and retained possession; {report['baseline_samples']} paired baseline samples")


if __name__ == '__main__':
    main()
