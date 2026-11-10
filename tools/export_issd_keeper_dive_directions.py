"""Export independently verified keeper dives from two isolated replays."""
import argparse
import json
import tempfile
from pathlib import Path
from export_issd_keeper_dive import export


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    cases=[('left',6,0,'keeper-synthetic-visible'),('right',2,4,'keeper-dive-direction4')]
    cycles={};evidence={};shared=None
    with tempfile.TemporaryDirectory() as tmp:
        for name,screen,direction,folder in cases:
            path=Path(tmp)/(name+'.json');report=export(a.root/folder,a.rom,path,direction)
            data=json.loads(path.read_text(encoding='utf8'))
            metadata={key:data[key] for key in ('rom_sha256','width','height','palette')}
            if shared is not None and metadata!=shared:raise ValueError('Incompatible keeper captures')
            shared=metadata;cycles[str(screen)]={'frames':data['frames'],'ticks':data['ticks']};evidence[name]=report
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'schema':'issd-keeper-dive-local/v2',**shared,'cycles':cycles},separators=(',',':')),encoding='utf8')
    a.report.write_text(json.dumps({'schema':'issd-keeper-dive-directions/v1','cases':evidence},indent=2)+'\n',encoding='utf8')


if __name__=='__main__':main()
