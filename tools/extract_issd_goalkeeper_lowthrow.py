"""Extract and validate the ROM's goalkeeper low-throw descriptor table.

The table and labels are static evidence. They do not prove when a throw is
triggered, how the ball moves, or how the poses are composed at runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles, lorom_offset

TABLE=0x82E80A
EXPECTED_SOURCES=(
    (0x8EDC5C,0x8EDE60,0x8EDFA4),
    (0x8EE128,0x8EE32C,0x8EE4B0),
    (0x8EE128,0x8EE32C,0x8EE4B0),
    (0x8EE128,0x8EE32C,0x8EE4B0),
    (0x8EDC5C,0x8EDE60,0x8EDFA4),
    (0x8EE634,0x8EE7D8,0x8EE97C),
    (0x8EE634,0x8EE7D8,0x8EE97C),
    (0x8EE634,0x8EE7D8,0x8EE97C),
)


def extract(rom_path, asm_path, focus_path):
    original=rom_path.read_bytes(); header=len(original)%0x8000
    if header not in (0,512) or hashlib.md5(original[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    rom=original[header:]; asm=asm_path.read_text(encoding='utf-8')
    pat=r'^DATA_([0-9A-F]{6}):\s*\n\s*dw[^\n]*\n\s*incbin "Graphics/DynamicSprites/([^"/]+)"'
    labels={int(a,16):name for a,name in re.findall(pat,asm,re.M)}
    if not re.search(r'CODE_84ECEF:.*?LDY\.w #DATA_82E80A\s+JSR\.w CODE_84E60C',asm,re.S):
        raise ValueError('Expected table selection missing from disassembly')
    transfer_pattern = (r'CODE_84E6C7:\s+STX\.b \$14\s+LDA\.b \$1E\s+BNE\.b CODE_84E6C0'
        r'\s+LDA\.w \$14E4\s+BNE\.b CODE_84E6BE\s+LDA\.w \$11E0'
        r'\s+CMP\.w \$11E2\s+BCS\.b CODE_84E6BE.*?'
        r'LDA\.l DATA_82A3D7&\$FF0000,x\s+STA\.b \$00')
    if not re.search(transfer_pattern,asm,re.S):
        raise ValueError('Descriptor/pose transfer order changed in disassembly')
    def word(addr):
        off=lorom_offset(addr);return int.from_bytes(rom[off:off+2],'little')
    slots=[]
    for direction in range(8):
        ptr=word(TABLE+2*direction);poses=[]
        for j in range(3):
            desc=word(0x820000|ptr+2*j)
            _,meta=descriptor_tiles(rom,desc)
            source=int(meta['graphics_source'][1:],16)
            if source!=EXPECTED_SOURCES[direction][j]:raise ValueError('Unexpected descriptor source')
            name=labels.get(source,'')
            if 'Goalie_' not in name or 'LowThrow' not in name:raise ValueError('Unexpected disassembly label')
            poses.append({'descriptor':desc,'pose_pointer':int(meta['pose'][1:],16),
                          'graphics_source':source,'disassembly_asset':name,'row_bytes':meta['row_bytes']})
        slots.append({'direction_index':direction,'descriptor_list':ptr,'poses':poses})
    start=lorom_offset(TABLE+16); timing=list(rom[start:start+4])
    if timing!=[4,4,20,0]:raise ValueError('Unexpected table bytes')
    focus=[]
    for line in focus_path.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        for actor in row.get('actors',[]):
            if actor.get('type')==1 and actor.get('animation_script')==0xE7C7:
                _,meta=descriptor_tiles(rom,actor['descriptor'])
                focus.append({'frame':row['frame'],'actor':actor['address'],
                  'state':actor['state'],'script':actor['animation_script'],
                  'descriptor':actor['descriptor'],'direction':actor['direction'],
                  'observed_pose':actor['pose'],'descriptor_pose':int(meta['pose'][1:],16),
                  'graphics_source':int(meta['graphics_source'][1:],16),
                  'part_count':len(actor.get('parts',[])),'ball':row.get('ball'),
                  'carrier':row.get('carrier')})
    if not focus or any(x['graphics_source']!=0xABF960 for x in focus):
        raise ValueError('Unexpected focused goalkeeper sample')
    return {'schema':'issd-goalkeeper-lowthrow-table/v1',
      'rom_sha256':hashlib.sha256(rom).hexdigest(),
      'disassembly_sha256':hashlib.sha256(asm_path.read_bytes()).hexdigest(),
      'focus_trace_sha256':hashlib.sha256(focus_path.read_bytes()).hexdigest(),
      'focused_caught_ball_samples':focus,
      'descriptor_pose_update':{'routine':0x84E6C7,'descriptor_field':0x14,'pose_field':0,
        'guards':['actor+$1E != 0','WRAM $14E4 != 0','WRAM $11E0 >= $11E2'],
        'effect':'descriptor is written before guards; pose changes only when guards allow transfer'},
      'trace_filter':'The source capture script excludes actors with pose >= $A000.',
      'table':TABLE,'selection_routine':0x84ECEF,'selection_helper':0x84E60C,
      'table_bytes_after_pointers':timing,'directions':slots,
      'limitations':['Direction indices are ROM values; screen orientation and mirroring require runtime validation.',
        'Table bytes and asset filenames do not by themselves establish full animation timing or semantics.',
        'Pose pointers and tiles require same-frame OAM, VRAM, CGRAM and PPU validation.',
        'Ball ownership, release conditions and physics remain unverified.',
        'The observed mismatch alone does not reveal which guard or event produced it.',
        'The focused capture excluded poses >= $A000 and cannot show direct ROM geometry at $D71A.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--asm',type=Path,default=Path('YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'))
    p.add_argument('--focus',type=Path,default=Path('docs/issd-focus-goalkeeper.jsonl'))
    a=p.parse_args();r=extract(a.rom,a.asm,a.focus)
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('OK: 8 direction slots and 24 verified descriptor references')

if __name__=='__main__':main()
