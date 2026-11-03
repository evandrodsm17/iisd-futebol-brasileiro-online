"""Compare a team/kit color table entry with captured PPU CGRAM."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_team_detail_colors import extract


def audit(rom,root):
    manifest=extract(rom);trace=root/'hair-runtime.jsonl';raw=trace.read_bytes()
    rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if not any(r.get('type')=='session_end' and r.get('steps')==120 for r in rows):raise ValueError('Incomplete replay')
    context=next((r for r in rows if r.get('type')=='context' and r['step']==1 and r['context']==0x0bd0),None)
    if not context or context['parent']!=0x1700:raise ValueError('Expected actor context absent')
    index=context['team2_index'];flags=context['team2_flags']
    if index%2 or index//2>=36:raise ValueError('Invalid team index')
    team=index//2;kit='away' if flags&8 else 'home';entry=manifest['teams'][team][kit]
    if entry['bgr555'] is None:raise ValueError('No-write selector cannot establish a palette color')
    frames=[]
    for row in rows:
        if row.get('type')!='graphics':continue
        cg=(root/f"frame-{row['step']:03d}-cgram.bin").read_bytes()
        if len(cg)!=512:raise ValueError('Invalid CGRAM dump')
        observed=int.from_bytes(cg[0xdc*2:0xdc*2+2],'little')&0x7fff
        if observed!=entry['bgr555']:raise ValueError(f"CGRAM mismatch step {row['step']}")
        frames.append({'step':row['step'],'frame':row['frame'],'bgr555':observed})
    if not frames:raise ValueError('No graphics frames')
    return {'schema':'issd-team-detail-color-audit/v1','source':{'path':trace.as_posix(),'sha256':hashlib.sha256(raw).hexdigest()},
            'rom_sha256':manifest['rom_sha256'],'team':team,'kit':kit,'team_index_word':index,'team_flags':flags,
            'selector':entry['selector'],'bgr555':entry['bgr555'],'cgram_index':'0xDC','frames':frames,
            'limitations':['Single observed team and kit; other table entries are static evidence only.',
                           'Synthetic positioning was used; live palette updates remain possible.',
                           'A zero selector means no write and cannot be treated as a specific color.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('root',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=audit(a.rom.read_bytes(),a.root)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Validated {len(result['frames'])} PPU colors for team {result['team']} {result['kit']}")
