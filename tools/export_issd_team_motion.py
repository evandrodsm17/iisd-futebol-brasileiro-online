"""Export ROM-palette team variants of validated walking/running OAM cycles."""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path
from PIL import Image

CYCLES={"running":([0xA749,0xA791,0xA7D9,0xA791,0xA749,0xA701,0xA6B9,0xA701],8),"walking":([0xA48B,0xA4E5,0xA53F,0xA4E5,0xA48B,0xA431,0xA3D7,0xA431],10)}
def renderer():
 p=Path(__file__).with_name("render_issd_descriptor_sprite.py");s=importlib.util.spec_from_file_location("r",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def trace(path):
 rows=[]
 for line in path.read_text(encoding="utf-8").splitlines():
  try: rows.append(json.loads(line))
  except json.JSONDecodeError: pass
 return rows
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument("rom",type=Path);a.add_argument("catalog",type=Path);a.add_argument("trace",type=Path);a.add_argument("output",type=Path);a.add_argument("--actor",type=lambda x:int(x,0),default=0x0D00);a.add_argument("--team",type=int,action="append");args=a.parse_args()
 r=renderer();rom=args.rom.read_bytes();rows=trace(args.trace);catalog=json.loads(args.catalog.read_text(encoding="utf-8"))
 for team in catalog["teams"]:
  if args.team and team["id"] not in args.team: continue
  for kit_name,kit in team["kit"].items():
   banks={index:r.parse_palette(kit["sprite_palette"]) for index in range(8)}
   for movement,(bases,length) in CYCLES.items():
    for direction,base in enumerate(bases):
     frames=[]
     for descriptor in [base+9*i for i in range(length)]:
      actor=next((x for row in rows for x in row["actors"] if x["address"]==args.actor and x["direction"]==direction and x["descriptor"]==descriptor),None)
      if actor is None: raise ValueError(f"missing ${descriptor:04X}, direction {direction}")
      tiles,_=r.descriptor_tiles(rom,descriptor,actor);frames.append(r.compose(tiles,r.normalise_parts(actor["parts"]),banks))
     cw=max(x.width for x in frames)+4;ch=max(x.height for x in frames)+4;sheet=Image.new("RGBA",(cw*len(frames),ch))
     for i,image in enumerate(frames):sheet.alpha_composite(image,(i*cw+(cw-image.width)//2,ch-image.height-2))
     out=args.output/f"{team['id']:02d}"/kit_name/f"{movement}-{direction}.png";out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out)
if __name__=="__main__":main()
