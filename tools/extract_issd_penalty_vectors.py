"""Extract penalty shot vector words into a local-only browser manifest."""
import argparse,hashlib,json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5

def extract(path):
 rom=path.read_bytes()
 if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected USA ROM')
 if rom[0x63d7c:0x63d7f]!=bytes([0x28,0,0x50]) or rom[0xddd8:0xdddd]!=bytes([1,9,8,10,2]):raise ValueError('Unexpected native tables')
 def signed(at):return int.from_bytes(rom[at:at+2],'little',signed=True)
 variants=[]
 for offset in rom[0x63d7c:0x63d7f]:
  directions=[]
  for base in range(5):
   i=offset+base*2
   directions.append({'dx':signed(0x63d95+i),'dy':signed(0x63d8b+i),'dz_clear':signed(0x63d9f+i),'dz_set':signed(0x63da9+i)})
  variants.append(directions)
 return {'schema':'issd-penalty-vectors/v1','rom_revision':'USA','variants':variants}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 data=extract(a.rom);a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
 print('OK: 30 native penalty vectors extracted locally')
