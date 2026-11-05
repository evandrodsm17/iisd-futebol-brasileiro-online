"""Validate one goalkeeper release pose against ROM geometry, PPU and screenshot.

Exports a transparent local preview only if every strict check succeeds.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image
from analyze_issd_draw_trace import slots
from audit_issd_goalkeeper_input_trials import audit as audit_inputs
from audit_issd_slide_timing_geometry import rom_parts
from compare_issd_oam_pixels import compose,compare,SIZES
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def export(root,baseline,rom_path,output,prepared,displayed,state):
    rom=rom_path.read_bytes();header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:]
    traces=[root/'trial.jsonl'];controls=[baseline/'trial.jsonl']
    result_input=audit_inputs(controls[0],traces,state)
    if result_input['trials'][0]['button']!='B':raise ValueError('Expected B trial')
    events=[json.loads(x) for x in (root/'keeper-transfers.jsonl').read_text(encoding='utf8').splitlines()]
    if not any(x.get('type')=='session_end' for x in events):raise ValueError('Incomplete capture')
    actor=0x500
    f=[x for x in events if x.get('type')=='keeper_frame' and x['actor']==actor and x['frame']==prepared]
    shot=[x for x in events if x.get('type')=='graphics' and x['actor']==actor and x['frame']==displayed]
    if len(f)!=1 or len(shot)!=1 or not all(shot[0][k] for k in ('ppu','cgram','screenshot')):raise ValueError('Missing capture')
    f=f[0];shot=shot[0]
    if f['direction']!=0:raise ValueError('Unexpected direction')
    draw=[json.loads(x) for x in (root/'keeper-draw.jsonl').read_text(encoding='utf8').splitlines()]
    indexes=[i for i,x in enumerate(draw) if x['frame']==prepared-1 and x['object']==actor]
    if len(indexes)!=1:raise ValueError('Missing draw entry')
    i=indexes[0]
    if i+1>=len(draw) or draw[i+1]['frame']!=prepared-1:raise ValueError('Missing next draw entry')
    candidates=slots(draw[i]['stack'],draw[i+1]['stack'])
    parts=rom_parts(rom,f['pose'])
    if len(parts)!=len(candidates):raise ValueError('OAM count differs')
    stem=shot['stem'];file=lambda suffix:root/(stem+suffix)
    oam=file('-ppu.bin').read_bytes();vram=file('-vram.bin').read_bytes();cgram=file('-cgram.bin').read_bytes()
    mirror=(root/f'keeper-{actor:04X}-{prepared}-mirror.bin').read_bytes();mirror=mirror[:512][::-1]+mirror[512:]
    origin=None;used=set();expected_tiles,meta=descriptor_tiles(rom,f['descriptor'])
    if int(meta['pose'][1:],16)!=f['pose']:raise ValueError('ROM pose mismatch')
    for slot,part in zip(candidates,parts):
        x,y,tile,prop=oam[4*slot:4*slot+4];hi=(oam[512+slot//4]>>(2*(slot%4)))&3
        if hi&1:x-=512
        if oam[4*slot:4*slot+4]!=mirror[4*slot:4*slot+4] or hi!=((mirror[512+slot//4]>>(2*(slot%4)))&3):raise ValueError('PPU and mirror differ')
        size=SIZES[shot['obsel']>>5][hi>>1]
        if size!=(16 if part['large'] else 8) or tile!=part['tile'] or prop!=0x28:raise ValueError('OAM part mismatch')
        dx=part['dx'] if part['dx']<32768 else part['dx']-65536;dy=part['dy'] if part['dy']<32768 else part['dy']-65536
        this=(x-dx+size//2,y-dy+size//2)
        if origin is None:origin=this
        if this!=origin:raise ValueError('Geometry origin differs')
        for ytile in range(size//8):
            for xtile in range(size//8):used.add((tile&0xf0)|((tile+xtile)&15) | (0 if ytile==0 else 16))
    base=(shot['obsel']&7)<<9
    for t in used:
        if expected_tiles[t*32:(t+1)*32]!=vram[(base+t)*32:(base+t+1)*32]:raise ValueError('ROM/VRAM tile mismatch')
    pixels=compose(oam,vram,cgram,shot['obsel'],candidates)
    with Image.open(file('-screen.png')) as image: result=compare(pixels,image)
    if not pixels:raise ValueError('No pixels')
    if result['nonmatching_pixels']:
        with Image.open(file('-screen.png')) as image:
            image=image.convert('RGB');miss={pos:image.getpixel(pos) for pos,color in pixels.items() if image.getpixel(pos)!=color}
        covered=set()
        for slot in range(max(candidates)):
            if slot in candidates:continue
            layer=compose(oam,vram,cgram,shot['obsel'],[slot]);covered.update(pos for pos,rgb in miss.items() if layer.get(pos)==rgb)
        if len(covered)!=len(miss):raise ValueError(f'Uncovered screenshot pixels {len(miss)-len(covered)}')
        result['covered_by_earlier_oam']=len(covered)
    preview=Image.new('RGBA',(96,96),(0,0,0,0))
    for (x,y),rgb in pixels.items():
        px=x-origin[0]+48;py=y-origin[1]+58
        if not (0<=px<96 and 0<=py<96):raise ValueError('Preview too small')
        preview.putpixel((px,py),(*rgb,255))
    output.parent.mkdir(parents=True,exist_ok=True);preview.save(output)
    return {'schema':'issd-goalkeeper-throw-pose-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
      'neutral_trial_sha256':sha(controls[0]),'capture_trial_sha256':sha(traces[0]),'trial_start':result_input['trials'][0]['start'],
      'trace_sha256':sha(root/'keeper-transfers.jsonl'),'draw_sha256':sha(root/'keeper-draw.jsonl'),
      'prepared_frame':prepared,'displayed_frame':displayed,'actor':actor,'script':f['script'],
      'descriptor':f['descriptor'],'pose':f['pose'],'direction':f['direction'],'graphics_source':meta['graphics_source'],
      'slots':candidates,'rom_geometry_parts':len(parts),'rom_vram_tile_indices':sorted(used),'screen':result,
      'preview_png_sha256':sha(output),
      'limitations':['One goalkeeper, one captured pose and palette, not an animation or validated team variants.',
        'Pixels overlapping another OAM object are corroborated by that object, but its identity is unconfirmed.',
        'A graphical match alone does not establish possession or ball-release physics.',
        'Other directions and the full sequence require synchronized captures.',
        'The 96x96 preview anchor is presentation-only.']}


