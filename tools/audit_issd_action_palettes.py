"""Compare captured PPU OBJ palette banks to the ROM-derived team catalogue."""
import argparse
import hashlib
import json
from pathlib import Path


def palette_hex(cgram, bank):
    if len(cgram) != 512 or not 0 <= bank < 8:
        raise ValueError('Expected 512-byte CGRAM and OBJ bank in range 0..7')
    result=[]
    for index in range(128 + bank*16, 128 + (bank+1)*16):
        word=int.from_bytes(cgram[index*2:index*2+2],'little')
        channels=(word&31,(word>>5)&31,(word>>10)&31)
        result.append('#' + ''.join(f'{v*255//31:02X}' for v in channels))
    return result


def matches(palette, teams):
    found=[]
    for team in teams:
        for kit, data in team.get('kit',{}).items():
            values=data.get('sprite_palette') if isinstance(data,dict) else None
            if values and len(values)==16 and [v.upper() for v in values]==palette:
                found.append({'team_id':team['id'],'team_name':team['name'],'kit':kit})
    return found


def audit(frame_audit, graphics, root, teams, script, direction):
    by_frame={row['frame']:row for row in graphics}; seen=set(); poses=[]
    if len(by_frame)!=len(graphics): raise ValueError('Duplicate frame')
    for frame in frame_audit['frames']:
        if frame['script']!=script or frame['direction']!=direction or frame['descriptor'] in seen: continue
        if not frame['candidate_pixels'] or frame['nonmatching_pixels']:
            raise ValueError('Cannot analyze unvalidated candidate pixels')
        source=by_frame[frame['ppu_frame']]
        oam=(root/source['oam_ppu']).read_bytes(); cgram=(root/source['cgram_ppu']).read_bytes()
        if len(oam)!=544: raise ValueError('Expected 544-byte PPU OAM')
        banks=sorted({(oam[s*4+3]>>1)&7 for s in frame['slots']})
        poses.append({'descriptor':frame['descriptor'],'ppu_frame':frame['ppu_frame'],
                      'slots':frame['slots'],'banks':[{'index':bank,'exact_catalog_matches':matches(palette_hex(cgram,bank),teams)} for bank in banks]})
        seen.add(frame['descriptor'])
    if not poses: raise ValueError('No validated poses in requested script and direction')
    return {'script':script,'direction':direction,'poses':poses,
            'limitations':['Full-bank color matches do not prove which team owns an actor.',
                           'A palette match alone does not establish transferability to other appearances or uniforms.',
                           'Catalog conversion uses 5-bit component times 255 divided by 31; screenshot conversion differs.',
                           'Candidate slots may omit hidden or occluded actor parts.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('frame_audit',type=Path);p.add_argument('graphics_trace',type=Path);p.add_argument('catalog',type=Path)
    p.add_argument('--script',type=lambda s:int(s,0),required=True);p.add_argument('--direction',type=int,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    def raw(path):return path.read_bytes()
    fa,gr,ca=map(raw,(a.frame_audit,a.graphics_trace,a.catalog))
    result=audit(json.loads(fa),[json.loads(line) for line in gr.splitlines() if line.strip()],a.graphics_trace.parent,json.loads(ca)['teams'],a.script,a.direction)
    result.update({'schema':'issd-action-palette-audit/v1','sources':[{'path':path.as_posix(),'sha256':hashlib.sha256(data).hexdigest()} for path,data in zip((a.frame_audit,a.graphics_trace,a.catalog),(fa,gr,ca))]})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('poses:',len(result['poses']))


if __name__=='__main__':main()
