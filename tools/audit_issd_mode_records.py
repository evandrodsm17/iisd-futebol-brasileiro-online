"""Audit whether the mode-record hooks fired during a completed gameplay route."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(hook_path, driver_path):
    hooks_raw, driver_raw = hook_path.read_bytes(), driver_path.read_bytes()
    hooks = [json.loads(line) for line in hooks_raw.splitlines()]
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if [h['site'] for h in hooks] != ['session_start', 'session_end']:
        raise ValueError('Expected a completed session without matching hooks')
    starts = [r for r in driver if r.get('type') == 'experiment_start']
    endings = [r for r in driver if r.get('type') == 'session_end']
    if len(starts) != 1 or len(endings) != 1 or not endings[0]['experiment_triggered']:
        raise ValueError('Driver did not reach its stable two-player scenario')
    samples = [r for r in driver if 'step' in r and 'actor' in r]
    if len(samples) < 100:
        raise ValueError('Too few gameplay observations')
    return {'schema': 'issd-mode-record-route/v1',
            'hook_trace_sha256': hashlib.sha256(hooks_raw).hexdigest(),
            'driver_trace_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'driver_scenario': 'two_player_action_observation, automated startup',
            'experiment_start_step': starts[0]['step'], 'end_step': endings[0]['steps'],
            'observed_driver_samples': len(samples), 'mode_helper_hook_count': 0,
            'limits': ['The hook trace and driver trace are paired by the local run, not by a cryptographic session identifier.',
                       'No hook only describes this startup path and observation window.',
                       'It does not rule out access through aliases, uninstrumented code or other game modes.',
                       'The natural meaning of the compared records and flag remains unknown.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ('hooks', 'driver', 'output'):
        p.add_argument(key, type=Path)
    a = p.parse_args()
    result = audit(a.hooks, a.driver)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: completed route; no mode hook in {result['observed_driver_samples']} samples")
