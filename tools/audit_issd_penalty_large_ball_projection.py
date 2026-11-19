"""Correlate the larger penalty-ball part, draw descriptor, and captured PPU pixels."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from compare_issd_oam_pixels import compose, compare, SIZES
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path, roots):
    rom = rom_path.read_bytes()
    if len(rom) % 0x8000 or hashlib.md5(rom).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected unheadered ROM')
    for offset, expected in {0x1539: bytes.fromhex('c2 20 b5 08 38 e9 04 00 85 18 38 e9 04 00 85 1c b5 0c 18 75 10 38 e9 04 00 85 1a 38 e9 04 00 85 1e'),
                             0x1924: bytes.fromhex('c2 20 a5 1e 18 79 00 40')}.items():
        if rom[offset:offset+len(expected)] != expected:
            raise ValueError(f'Unexpected projection instructions at {offset:x}')
    captures = []
    for root, direction in zip(roots, ('Left', 'Right')):
        raw = (root/'graphics.jsonl').read_bytes()
        rows = [json.loads(line) for line in raw.splitlines()]
        if rows[0].get('type') != 'capture_start' or rows[-1].get('type') != 'capture_end' or any(e.get('type') == 'error' for e in rows):
            raise ValueError('Incomplete graphics capture')
        driver_path, = root.glob('issd-auto-probe-*.jsonl')
        driver_raw = driver_path.read_bytes()
        driver = [json.loads(line) for line in driver_raw.splitlines()]
        configs = [e for e in driver if e.get('type') == 'penalty_direction_config']
        if len(configs) != 1 or configs[0].get('direction') != direction or configs[0].get('controllers') != 'both':
            raise ValueError('Unexpected synthetic inputs')
        if not any(e.get('type') == 'synthetic_score' for e in driver) or not any(e.get('type') == 'synthetic_clock' for e in driver) or not any(e.get('type') == 'session_end' for e in driver):
            raise ValueError('Incomplete synthetic driver')
        samples = [e for e in rows if e.get('type') == 'full_graphics']
        if [e['delta'] for e in samples] != list(range(1,41)):
            raise ValueError('Incomplete frame capture')
        draws, parts = {}, {}
        for e in rows:
            if e.get('type') == 'draw_entry':
                draws.setdefault(e['frame'], []).append(e)
            if e.get('type') == 'ball_part' and e['object'] == 0x700 and e['size'] == 16:
                parts.setdefault(e['frame'], []).append(e)
        results = []
        for sample in samples:
            stem = sample['stem']
            oam, vram, cgram = [(root/f'{stem}-{kind}.bin').read_bytes() for kind in ('oam','vram','cgram')]
            image_path = root/f'{stem}.png'
            candidates = []
            for lag in (1,2,3,4):
                frame = sample['frame']-lag
                draw = draws.get(frame, [])
                indexes = [i for i,e in enumerate(draw) if e['object'] == 0x700]
                part = parts.get(frame, [])
                if len(indexes) != 1 or indexes[0]+1 >= len(draw) or len(part) != 1:
                    continue
                i = indexes[0]; obj = draw[i]; part = part[0]
                selected = slots(obj['stack'], draw[i+1]['stack'])
                if len(selected) != 1:
                    continue
                slot = selected[0]
                x,y,tile,props = oam[4*slot:4*slot+4]
                high = (oam[512+slot//4] >> (2*(slot%4))) & 3
                size = SIZES[(sample['obsel'] >> 5) & 7][high >> 1]
                if high & 1 or size != 16 or tile not in (0x40,0x42,0x44) or props != 0x3f:
                    continue
                pixels = compose(oam,vram,cgram,sample['obsel'],selected)
                with Image.open(image_path) as image:
                    comparison = compare(pixels,image)
                if comparison['candidate_pixels'] != 68 or comparison['exact_rgb_matches'] != 68:
                    continue
                expected_x = (obj['object_x']-8+part['offset_x']) & 255
                expected_y = (obj['object_y']+obj['object_height']-8+part['offset_y']) & 255
                candidates.append({'lag':lag,'draw_frame':frame,'slot':slot,'tile':tile,
                                   'object_x':obj['object_x'],'object_y':obj['object_y'],'object_height':obj['object_height'],
                                   'offset_x':part['offset_x'],'offset_y':part['offset_y'],
                                   'oam_x':x,'oam_y':y,'expected_x':expected_x,'expected_y':expected_y,
                                   'matches_both':x==expected_x and y==expected_y})
            if any(c['lag'] == 2 for c in candidates):
                results.append({'frame':sample['frame'],'matching_pixels':68,
                                'screenshot_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'candidates':candidates})
        if not results:
            raise ValueError('No visible large-ball candidates')
        two_back = [c for result in results for c in result['candidates'] if c['lag']==2]
        if len(two_back) != len(results) or not all(c['matches_both'] and c['offset_x']==0 and c['offset_y']==0xfffc for c in two_back):
            raise ValueError('Unexpected lag-two projection')
        counts = {str(lag):sum(c['matches_both'] for result in results for c in result['candidates'] if c['lag']==lag) for lag in (1,2,3,4)}
        totals = {str(lag):sum(1 for result in results for c in result['candidates'] if c['lag']==lag) for lag in (1,2,3,4)}
        captures.append({'name':root.name,'input_direction':direction,'graphics_sha256':hashlib.sha256(raw).hexdigest(),
                         'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'matched_frames':len(results),
                         'matched_by_lag':counts,'candidates_by_lag':totals,'samples':results})
    if [c['matched_frames'] for c in captures] != [6,5]:
        raise ValueError('Unexpected capture sample count')
    return {'schema':'issd-penalty-large-ball-projection/v1','rom_offsets_checked':['0x1539','0x1924'],
            'captures':captures,'limits':['Two synthetic captures with Left and Right applied to both controllers.',
            'Only frames with a lag-two 16x16 candidate, selected tiles and 68 exactly matching opaque pixels are included.',
            'All pixel-compatible candidate lags are retained; matches do not establish universal timing.',
            'Other sprites, mirrored paths, occlusion, priority and configurations remain unvalidated.',
            'ROM, screenshots and raw PPU captures remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom','left','right','output'):
        parser.add_argument(name,type=Path)
    args = parser.parse_args()
    result = audit(args.rom,[args.left,args.right])
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for capture in result['captures']:
        print(capture['name'],capture['matched_frames'],capture['matched_by_lag'],capture['candidates_by_lag'])
