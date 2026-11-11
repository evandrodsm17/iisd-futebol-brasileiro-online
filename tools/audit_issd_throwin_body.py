"""Validate recorded throw-in body geometry against ROM, OAM and screenshots.

All capture files and the ROM remain local. Missing draw samples are reported,
not interpolated. A matching body does not establish auxiliary hair or timing.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_actor_oam_properties import derive, SIZES
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_oam_pixels import compose, compare


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actual(oam, part, obsel):
    slot = part['slot']
    x, y, tile, attr = oam[slot * 4:slot * 4 + 4]
    high = (oam[512 + slot // 4] >> (2 * (slot % 4))) & 3
    return {'slot': slot, 'x': x - 512 if high & 1 else x, 'y': y,
            'tile': tile, 'attr': attr, 'size': SIZES[obsel >> 5][high >> 1]}


def audit(root, rom_path, actor, skip_screen_mismatch=False, validate_ball_overlay=False):
    rom = rom_path.read_bytes()
    if hashlib.sha256(rom).hexdigest() != 'd2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9':
        raise ValueError('Unexpected ROM revision')
    draw_path = root / 'slide-draw.jsonl'
    events = [json.loads(line) for line in draw_path.read_text().splitlines() if line.strip()]
    poses = {r['frame']: r for r in map(json.loads, (root / 'slide-poses.jsonl').read_text().splitlines())}
    results, missing, screen_mismatches = [], [], []
    for frame in sorted(poses):
        if frame + 1 not in poses:
            continue
        draw = [r for r in events if not r.get('type') and r['frame'] == frame - 1]
        indices = [i for i, row in enumerate(draw) if row['object'] == actor]
        geometry = [r for r in events if r.get('type') == 'body_geometry' and r['frame'] == frame - 1 and r['object'] == actor]
        if len(indices) != 1 or indices[0] + 1 >= len(draw) or len(geometry) != 1:
            missing.append(frame)
            continue
        g, i = geometry[0], indices[0]
        capture, displayed = poses[frame], poses[frame + 1]
        if g['source'] != 'rom88' or g['parts'] != rom_parts(rom, g['pose']) or g['descriptor'] != capture['descriptor']:
            raise ValueError(f'ROM geometry mismatch at frame {frame}')
        candidates = slots(draw[i]['stack'], draw[i + 1]['stack'])
        parts = derive(g, g, capture['obsel'], candidates)
        mirror = (root / (capture['stem'] + '-mirror.bin')).read_bytes()
        mirror = mirror[:512][::-1] + mirror[512:]
        ppu = (root / (displayed['stem'] + '-ppu.bin')).read_bytes()
        if any(part != actual(mirror, part, capture['obsel']) or part != actual(ppu, part, capture['obsel']) for part in parts):
            raise ValueError(f'OAM mismatch at frame {frame}')
        pixels = compose(ppu, (root / (displayed['stem'] + '-vram.bin')).read_bytes(),
                         (root / (displayed['stem'] + '-ppu-cgram.bin')).read_bytes(), displayed['obsel'], candidates)
        with Image.open(root / (displayed['stem'] + '-screen.png')) as screen:
            comparison = compare(pixels, screen)
        overlay_slots = []
        body_comparison = comparison
        if comparison['nonmatching_pixels'] and validate_ball_overlay:
            ball_indices = [i for i, row in enumerate(draw) if row['object'] == 0x400]
            if len(ball_indices) == 1 and ball_indices[0] + 1 < len(draw):
                b = ball_indices[0]
                overlay_slots = slots(draw[b]['stack'], draw[b + 1]['stack'])
                if set(overlay_slots) & set(candidates):
                    raise ValueError(f'Ball and body overlap OAM slots at frame {frame}')
                combined = compose(ppu, (root / (displayed['stem'] + '-vram.bin')).read_bytes(),
                                   (root / (displayed['stem'] + '-ppu-cgram.bin')).read_bytes(),
                                   displayed['obsel'], candidates + overlay_slots)
                with Image.open(root / (displayed['stem'] + '-screen.png')) as screen:
                    comparison = compare(combined, screen)
        if not comparison['candidate_pixels'] or comparison['nonmatching_pixels']:
            if skip_screen_mismatch:
                screen_mismatches.append({'prepared_frame': frame, 'descriptor': g['descriptor'], **comparison})
                continue
            raise ValueError(f'Screen pixels do not match at frame {frame}: {comparison}')
        results.append({'prepared_frame': frame, 'displayed_frame': frame + 1,
                        'descriptor': g['descriptor'], 'pose': g['pose'], 'slots': candidates,
                        'ball_slots': overlay_slots, 'body_only_mismatches': body_comparison['nonmatching_pixels'],
                        'parts': len(parts), **comparison})
    if not results:
        raise ValueError('No validated frames')
    return {'schema': 'issd-throw-body-audit/v1', 'rom_sha256': digest(rom_path),
            'draw_sha256': digest(draw_path), 'poses_sha256': digest(root / 'slide-poses.jsonl'),
            'actor': actor, 'frames': results, 'missing_frames': missing, 'screen_mismatches': screen_mismatches,
            'limitations': ['One replay and one direction; no generalized timing or appearance.',
                            'Screen comparison validates visible pixels; obscured body pixels rely on ROM geometry and OAM evidence. Hair is not established.',
                            'Missing frames are not inferred; no complete animation is asserted.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--actor', type=lambda value: int(value, 0), required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--validate-ball-overlay', action='store_true', help='validate the captured ball and body together when they overlap')
    parser.add_argument('--skip-screen-mismatch', action='store_true', help='report mismatched frames separately; never treat them as validated')
    args = parser.parse_args()
    report = audit(args.root, args.rom, args.actor, args.skip_screen_mismatch, args.validate_ball_overlay)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"Validated {len(report['frames'])} frames; {len(report['missing_frames'])} missing draw samples; {len(report['screen_mismatches'])} screen mismatches")
