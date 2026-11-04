"""Export only hair tiles and anchors audited during local pass replays."""
import argparse,base64,hashlib,json
from pathlib import Path
from audit_issd_pass_hair import audit


def export(root,rom_path,state,output):
 report=audit(root,rom_path,state);rom=rom_path.read_bytes();styles={}
 for style,case in report['cases'].items():
  frames=[]
  for entry in case['frames']:
   tile=rom[entry['rom_file_offset']:entry['rom_file_offset']+32]
   if hashlib.sha256(tile).hexdigest()!=entry['tile_sha256']:raise ValueError('Tile changed')
   frames.append({'descriptor':entry['descriptor'],'x':entry['relative_x'],'y':entry['relative_y'],'h_flip':bool(entry['attr']&0x40),'v_flip':bool(entry['attr']&0x80),'tile':base64.b64encode(tile).decode('ascii')})
  styles[style]=frames
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps({'schema':'issd-pass-hair-local/v1','rom_sha256':report['rom_sha256'],'screen_direction':2,'styles':styles,'limitations':['Synthetic context assignment; one actor, direction and action.','ROM-derived graphics are local only.']},separators=(',',':')),encoding='utf-8')
 return len(styles)


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--rom',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();print('exported local pass hair styles:',export(a.root,a.rom,a.state,a.output))
