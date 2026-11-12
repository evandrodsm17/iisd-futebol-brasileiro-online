"""Summarize a synthetic fast competition navigation without inferring game rules."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def sha(data): return hashlib.sha256(data).hexdigest()


def audit(driver_path, hook_path, screenshot_path):
    driver_raw, hook_raw, screenshot = driver_path.read_bytes(), hook_path.read_bytes(), screenshot_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    config = [r for r in driver if r.get('type') == 'competition_config']
    ending = [r for r in driver if r.get('type') == 'session_end']
    clocks = [r for r in driver if r.get('type') == 'synthetic_clock']
    scores = [r for r in driver if r.get('type') == 'synthetic_score']
    if len(config) != 1 or config[0]['menu_mode'] != 'world_series' or not config[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Unexpected competition configuration')
    if len(ending) != 1 or ending[0]['steps'] != 26000 or ending[0]['reason'] != 'frame_limit':
        raise ValueError('Incomplete navigation')
    if len(scores) != 5 or len(clocks) != 10 or collections.Counter(r['phase'] for r in clocks) != {0: 5, 1: 5}:
        raise ValueError('Unexpected synthetic match interventions')
    if [h['site'] for h in hooks] != ['session_start', 'session_end']:
        raise ValueError('Mode hooks changed; inspect before reporting absence')
    if not screenshot.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Missing screenshot')
    menu_steps = [r for r in driver if r.get('input') == 'synthetic-menu-A']
    if not menu_steps:
        raise ValueError('No synthetic menu navigation found')
    return {'schema': 'issd-competition-route/v1', 'driver_sha256': sha(driver_raw), 'hook_trace_sha256': sha(hook_raw),
            'menu_screenshot_sha256': sha(screenshot), 'menu_screenshot_step': 23400,
            'configured_mode': 'world_series', 'observed_menu_route': 'open_game / short_league', 'final_step': ending[0]['steps'],
            'synthetic_clock_writes': clocks, 'synthetic_score_writes': scores,
            'mode_hook_count': 0, 'synthetic_menu_samples': len(menu_steps),
            'limits': ['The historical automation selected Open Game / Short League, despite the world_series configuration label.',
                       'Clock, score and some menu inputs were changed synthetically in a disposable emulator.',
                       'The screenshot was visually inspected as a standings menu; no OCR or gameplay semantics are inferred.',
                       'A negative hook observation covers only the instrumented routines and this route.',
                       'The traces and screenshot are paired by this local run, not a cryptographic session identifier.',
                       'ROM, savestate, screenshot and raw traces are not distributed.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('driver', 'hooks', 'screenshot', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    result = audit(a.driver, a.hooks, a.screenshot)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: 5 synthetic matches, 10 clock writes, observed standings menu')
