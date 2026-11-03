"""Compare the generated local body preview against captured PPU pixels."""
import argparse
import base64
import json
from pathlib import Path
from compare_issd_oam_pixels import compose


def verify(root,preview,evidence):
    data=json.loads(preview.read_text(encoding='utf-8'))
    captures={r['frame']:r for r in (json.loads(x) for x in (root/'slide-poses.jsonl').read_text().splitlines() if x.strip())}
    geometry=[r for r in (json.loads(x) for x in (root/'slide-draw.jsonl').read_text().splitlines() if x.strip()) if r.get('type')=='body_geometry']
    frames=json.loads(evidence.read_text(encoding='utf-8'))['frames']
    if len(data['frames'])!=len(frames): raise ValueError('Frame count mismatch')
    for frame,entry in zip(data['frames'],frames):
        if frame['descriptor']!=entry['descriptor']: raise ValueError('Descriptor mismatch')
        rows=[x for x in geometry if x['frame']==entry['draw_frame']]
        if len(rows)!=1: raise ValueError('Missing geometry')
        g=rows[0];capture=captures[entry['displayed_frame']];stem=capture['stem']
        oam=(root/(stem+'-ppu.bin')).read_bytes();cgram=(root/(stem+'-ppu-cgram.bin')).read_bytes()
        original=compose(oam,(root/(stem+'-vram.bin')).read_bytes(),cgram,capture['obsel'],entry['slots'])
        shifted={(x+48-g['draw_x'],y+60-((g['draw_y']+g['draw_z'])&65535)):rgb for (x,y),rgb in original.items()}
        local_oam=bytearray(544);local_vram=bytearray(65536)
        for tile in frame['tiles']:
            value=base64.b64decode(tile['data'],validate=True)
            if len(value)!=32:raise ValueError('Invalid tile')
            local_vram[tile['address']:tile['address']+32]=value
        for part in frame['parts']:
            i=part['slot'];local_oam[4*i:4*i+4]=bytes((part['x'],part['y'],part['tile'],part['attr']))
            local_oam[512+i//4]|=(2 if part['size']==16 else 0)<<(2*(i%4))
        local=compose(bytes(local_oam),bytes(local_vram),base64.b64decode(frame['cgram'],validate=True),frame['obsel'],entry['slots'])
        if local!=shifted: raise ValueError(f"Pixel mismatch in descriptor {frame['descriptor']:04X}")
    return len(frames)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('preview',type=Path);p.add_argument('evidence',type=Path)
    a=p.parse_args();print('poses coincidentes:',verify(a.root,a.preview,a.evidence))
