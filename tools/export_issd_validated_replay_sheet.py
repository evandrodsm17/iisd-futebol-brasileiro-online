"""Export transparent diagnostic poses only from exact screenshot-matched replay frames."""
import argparse
import json
from pathlib import Path

from PIL import Image
from compare_issd_oam_pixels import compare, compose


def export(audit, graphics, root, output, script, direction):
    by_frame = {row['frame']: row for row in graphics}
    selected = {}
    required = []
    for row in audit['frames']:
        if row['script'] != script or row['direction'] != direction: continue
        if row['descriptor'] not in required: required.append(row['descriptor'])
        if row['candidate_pixels'] and not row['nonmatching_pixels']:
            selected.setdefault(row['descriptor'], row)
    if any(descriptor not in selected for descriptor in required):
        raise ValueError('At least one descriptor has no exact screenshot-matched frame')
    if not selected: raise ValueError('No validated frames selected')
    poses = []
    for descriptor in required:
        row = selected[descriptor]
        source = by_frame[row['ppu_frame']]
        pixels = compose((root / source['oam_ppu']).read_bytes(), (root / source['vram']).read_bytes(),
                         (root / source['cgram_ppu']).read_bytes(), source['obsel'], row['slots'])
        with Image.open(root / source['screenshot']) as image: metrics = compare(pixels, image)
        if metrics['nonmatching_pixels'] or not metrics['candidate_pixels']:
            raise ValueError('Current capture does not reproduce the validated pixels')
        poses.append((descriptor, row, pixels))
    positions = [xy for _, _, pixels in poses for xy in pixels]
    left, top = min(x for x, y in positions), min(y for x, y in positions)
    right, bottom = max(x for x, y in positions) + 1, max(y for x, y in positions) + 1
    width, height = right - left, bottom - top
    sheet = Image.new('RGBA', (width * len(poses), height), (0, 0, 0, 0))
    for column, (_, _, pixels) in enumerate(poses):
        for (x, y), rgb in pixels.items(): sheet.putpixel((column * width + x - left, y - top), (*rgb, 255))
    sheet.save(output)
    return {'script': script, 'direction': direction, 'cell_size': [width, height],
            'screen_origin': [left, top], 'descriptors': [d for d, _, _ in poses],
            'ppu_frames': [r['ppu_frame'] for _, r, _ in poses],
            'limitations': ['Diagnostic only: exact candidate pixels do not prove complete actor coverage.',
                            'Colors represent the captured game state, not all teams or uniforms.',
                            'No animation timing or gameplay semantics is inferred.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audit',type=Path);p.add_argument('graphics',type=Path)
    p.add_argument('--script',type=lambda s:int(s,0),required=True);p.add_argument('--direction',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    audit=json.loads(a.audit.read_text(encoding='utf-8'))
    graphics=[json.loads(line) for line in a.graphics.read_text(encoding='utf-8').splitlines() if line.strip()]
    result=export(audit,graphics,a.graphics.parent,a.output,a.script,a.direction)
    a.output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('poses:',len(result['descriptors']),'cell:',result['cell_size'])


if __name__=='__main__': main()
