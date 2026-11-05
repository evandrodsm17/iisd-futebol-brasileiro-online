"""Combine independently verified shot captures; never synthesize missing directions."""
import argparse
import json
import tempfile
from pathlib import Path
from export_issd_shot_body import export

CASES = [('Right',2,0),('Up',0,6),('UpRight',1,7),('DownRight',3,1),('Down',4,2),('DownLeft',5,3),('Left',6,4),('UpLeft',7,5)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    cycles={};evidence={};shared=None
    with tempfile.TemporaryDirectory() as temp:
        for name,screen,direction in CASES:
            root=a.root/('shot-body-replay' if name=='Right' else 'shot-pre-UpRight' if name=='UpRight' else 'shot-search-'+name+'-380' if name in ('UpLeft','DownLeft') else 'shot-facing-'+name)
            path=Path(temp)/(name+'.json');report=export(root,a.rom,path,screen,direction)
            data=json.loads(path.read_text(encoding='utf8'))
            metadata={k:data[k] for k in ('rom_sha256','palette','extra_palette','palette10','team_palette')}
            if shared is not None and metadata!=shared:raise ValueError('Incompatible capture palettes or ROM')
            shared=metadata;cycles[str(screen)]={'width':96,'height':96,'frames':data['frames']};evidence[name]=report
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'schema':'issd-shot-body-local/v2',**shared,'cycles':cycles},separators=(',',':')),encoding='utf8')
    a.report.write_text(json.dumps({'schema':'issd-shot-directions-evidence/v1','cases':evidence},indent=2)+'\n',encoding='utf8')


if __name__=='__main__':main()
