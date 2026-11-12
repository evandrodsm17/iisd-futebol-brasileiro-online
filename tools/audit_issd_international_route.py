"""Summarize a visually verified, synthetic International-mode navigation."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def sha(data): return hashlib.sha256(data).hexdigest()


def audit(driver_path, hook_path, menu_path, match_path):
    driver_raw, hook_raw = driver_path.read_bytes(), hook_path.read_bytes()
    menu, match = menu_path.read_bytes(), match_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    config = [r for r in driver if r.get('type') == 'competition_config']
    ending = [r for r in driver if r.get('type') == 'session_end']
    clocks = [r for r in driver if r.get('type') == 'synthetic_clock']
    scores = [r for r in driver if r.get('type') == 'synthetic_score']
    menu_input = [r for r in driver if r.get('step') == 1170 and r.get('input') == 'Down']
    if len(config) != 1 or config[0]['menu_mode'] != 'international' or not config[0]['synthetic_fast_clock_and_score'] or not menu_input:
        raise ValueError('Unexpected configured mode or menu input')
    if len(ending) != 1 or ending[0]['steps'] != 26000 or ending[0]['reason'] != 'frame_limit':
        raise ValueError('Incomplete session')
    if len(scores) != 6 or len(clocks) != 12 or collections.Counter(r['phase'] for r in clocks) != {0: 6, 1: 6}:
        raise ValueError('Unexpected synthetic interventions')
    if [h['site'] for h in hooks] != ['session_start', 'session_end']:
        raise ValueError('Hooks fired or session failed; manual review needed')
    if not menu.startswith(b'\x89PNG\r\n\x1a\n') or not match.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Missing screenshot')
    return {'schema': 'issd-international-route/v1', 'driver_sha256': sha(driver_raw), 'hook_trace_sha256': sha(hook_raw),
            'menu_screenshot_sha256': sha(menu), 'menu_screenshot_step': 1200,
            'match_screenshot_sha256': sha(match), 'match_screenshot_step': 10200,
            'configured_mode': 'international', 'final_step': ending[0]['steps'],
            'synthetic_clock_writes': clocks, 'synthetic_score_writes': scores, 'mode_hook_count': 0,
            'limits': ['Menu and match screenshots were visually inspected, not recognized by OCR.',
                       'Clock, score and some menu inputs were changed synthetically in a disposable emulator.',
                       'Six score interventions do not prove tournament completion or naturally produced results.',
                       'Negative hook observation covers only these instrumented routines and this route.',
                       'Artifacts were paired by the isolated local run; no cryptographic session identity exists.',
                       'ROM, screenshot and raw traces are not distributed.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('driver', 'hooks', 'menu_screenshot', 'match_screenshot', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    result = audit(a.driver, a.hooks, a.menu_screenshot, a.match_screenshot)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: verified International route and six synthetic score interventions')
