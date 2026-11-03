"""Compare hair-style VRAM/OAM evidence across isolated match replays."""
import argparse
import hashlib
import json
from pathlib import Path
from analyze_issd_hair_oam import analyze as analyze_oam
from analyze_issd_hair_vram import analyze as analyze_vram


def summarize(rom,cases):
    result=[]
    for style,root in cases:
        trace=root/'hair-runtime.jsonl';raw=trace.read_bytes()
        rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        mutations=[r for r in rows if r.get('type')=='synthetic_hair']
        if style==1:
            if mutations:raise ValueError('Reference style must not be overridden')
        elif len(mutations)!=1 or mutations[0]['style']!=style or mutations[0]['actor']!=0x1700:
            raise ValueError('Missing or incorrect synthetic hair change')
        vram=analyze_vram(rom,rows);oam=analyze_oam(root)
        if len(vram['contexts'])!=1 or vram['contexts'][0]['atlas_style']!=style:
            raise ValueError('Observed atlas style does not match test')
        frames=oam['frames']
        result.append({'style':style,'synthetic_hair':bool(mutations),
          'trace':trace.as_posix(),'trace_sha256':hashlib.sha256(raw).hexdigest(),
          'vram_counts':vram['counts'],'oam_frames':len(frames),'direct_exact_frames':oam['exact_nonempty'],
          'prior_oam_matching_pixels':sum(f['earlier_slot_rgb_matches'] for f in frames),
          'unexplained_pixels':sum(f['unexplained_after_earlier_slots'] for f in frames),
          'palettes':sorted({f['hair_oam']['palette'] for f in frames})})
    if [item['style'] for item in result]!=[1,2,13]:raise ValueError('Expected styles 1, 2, 13')
    return {'schema':'issd-hair-style-trials/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'cases':result,'limitations':['Actor position was changed in RAM in each replay.',
            'Styles 2 and 13 were forced in the auxiliary context, not selected through gameplay.',
            'Prior OAM RGB matches suggest occlusion but do not establish complete priority behavior.',
            'Only one actor, one movement direction and one OBJ palette were observed.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path)
    p.add_argument('style1',type=Path);p.add_argument('style2',type=Path);p.add_argument('style13',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=summarize(a.rom.read_bytes(),[(1,a.style1),(2,a.style2),(13,a.style13)])
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('Validated styles:',', '.join(str(c['style']) for c in result['cases']))
