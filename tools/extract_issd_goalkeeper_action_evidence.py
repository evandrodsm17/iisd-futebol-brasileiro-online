"""Correlate observed keeper dive descriptors with USA ROM graphic sources.

Asset filenames are labels from the disassembly, not proof of game semantics.
This emits metadata only: never ROM bytes, tiles, or reconstructed images.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles

SCRIPTS = {0xE924, 0xE94B, 0xE996, 0xE9CD, 0xEA18}


def extract(rom_path, trace_path, asm_path):
    rom = rom_path.read_bytes()
    header = len(rom) % 0x8000
    if header not in (0, 512) or hashlib.md5(rom[header:]).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    rom = rom[header:]
    asm = asm_path.read_text(encoding='utf-8')
    pattern = r'^DATA_([0-9A-F]{6}):\s*\n\s*dw[^\n]*\n\s*incbin "Graphics/DynamicSprites/([^"/]+)"'
    labels = {int(addr, 16): name for addr, name in re.findall(pattern, asm, re.M)}
    observed = {}
    for line in trace_path.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        for actor in row.get('actors', []):
            script = actor.get('animation_script')
            if actor.get('type') != 1 or script not in SCRIPTS:
                continue
            desc = actor['descriptor']
            _, meta = descriptor_tiles(rom, desc)
            source = int(meta['graphics_source'][1:], 16)
            name = labels.get(source)
            if not name or not name.startswith('GFX_Sprite_Goalie_'):
                raise ValueError(f'Unresolved keeper source ${source:06X}')
            if int(meta['pose'][1:], 16) != actor['pose']:
                raise ValueError(f'Pose mismatch at frame {row["frame"]}')
            key = (script, desc, actor['direction'], source, name)
            entry = observed.setdefault(key, {'frames': [], 'actors': set(), 'states': set()})
            entry['frames'].append(row['frame'])
            entry['actors'].add(actor['address'])
            entry['states'].add(actor['state'])
    samples = []
    for (script, desc, direction, source, name), entry in sorted(observed.items()):
        samples.append({'script': script, 'descriptor': desc, 'direction': direction,
            'graphics_source': source, 'disassembly_asset': name,
            'sample_count': len(entry['frames']), 'frames': entry['frames'],
            'actors': sorted(entry['actors']), 'states': sorted(entry['states'])})
    assets = sorted(set(re.findall(r'GFX_Sprite_Goalie_[^"/]+\.bin', asm)))
    families = {key: [x for x in assets if key.lower() in x.lower()] for key in ('LowThrow','CaughtBall','Dive')}
    return {'schema':'issd-goalkeeper-action-evidence/v1',
        'rom_sha256': hashlib.sha256(rom).hexdigest(),
        'trace_sha256': hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        'disassembly_sha256': hashlib.sha256(asm_path.read_bytes()).hexdigest(),
        'observed': samples, 'disassembly_asset_families': families,
        'limitations': ['Names are supplied by disassembly; semantic meaning requires runtime validation.',
            'Trace samples are not necessarily consecutive frames.',
            'Observed geometry is not a same-frame PPU/VRAM/CGRAM validation.',
            'Asset families are static labels and do not establish animation order or timing.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--trace',type=Path,default=Path('docs/issd-natural-play-trace.jsonl'))
    p.add_argument('--asm',type=Path,default=Path('YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); report=extract(a.rom,a.trace,a.asm)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"OK: {len(report['observed'])} observed descriptor/direction combinations")

if __name__=='__main__':main()

