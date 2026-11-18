"""Audit a second pair of isolated controller trials using Right."""
import argparse
import json
from pathlib import Path
from audit_issd_penalty_isolated_inputs import audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('p1', 'p2', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    expected = [(2, 6), (2, 26), (2, 12)]
    result = {'schema': 'issd-penalty-isolated-right/v1',
              'runs': [audit(args.p1, 'p1', expected, 'Right'), audit(args.p2, 'p2', expected, 'Right')],
              'limits': ['One comparable penalty per run; action pulses still reached both controllers.',
                         'Identical results do not prove the controllers are interchangeable.',
                         'Synthetic score, clock and inputs; ROM and raw traces remain local.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: isolated Right direction trials audited')
