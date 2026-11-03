"""Extract local editor-preview data; never copies the ROM into the web app."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import decompress, lorom_offset


def word(data, offset):
    if offset<0 or offset+2>len(data):raise ValueError('ROM offset out of range')
    return int.from_bytes(data[offset:offset+2],'little')


def tile(raw, index):
    block=raw[index*32:(index+1)*32]
    if len(block)!=32:raise ValueError('Incomplete tile')
    return [[sum(((block[(p//2)*16+y*2+p%2]>>(7-x))&1)<<p for p in range(4))
             for x in range(8)] for y in range(8)]


def colours(rom,team,goalie=False,alternate=False):
    def pal(table,count):
        ptr=word(rom,table+team*2)
        if not ptr:return None
        pos=lorom_offset(0x890000|ptr)+2
        return [word(rom,pos+i*2) for i in range(count)]
    kit=pal(0x10326 if goalie else 0x1027a,11 if goalie else 16)
    if not kit:raise ValueError('Missing team palette')
    colors=([0]+kit+[0]*4) if goalie else kit[:]
    if alternate:
        skin=pal(0x1037c,5);hair=pal(0x103d2,1)
        if skin:colors[2:7]=skin
        if hair:colors[1]=hair[0]
    return colors


def extract(rom):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Selecione a ROM original ISS Deluxe USA')
    rom=rom[header:]
    def signed(x):return x if x<128 else x-256
    def geom(address):
        raw,interleaved=decompress(rom,address)
        if interleaved:raise ValueError('Unexpected geometry format')
        count=word(raw,1);base=3+raw[0]
        if len(raw)<base+count*4:raise ValueError('Incomplete geometry')
        return raw,count,base
    geometry={False:geom(0x988472),True:geom(0x988b61)}
    heads,heads_count,heads_base=geom(0x9890cc)
    hair_tiles=[]
    for style in range(1,14):
        at=0xed6d+(style-1)*4
        address=int.from_bytes(rom[at:at+3],'little');offset=lorom_offset(address)
        atlas=rom[offset:offset+24*32]
        hair_tiles.append([base64.b64encode(bytes(sum(tile(atlas,n),[]))).decode('ascii') for n in range(24)])
    descriptors={};head_positions={}
    for goalie in (False,True):
        frames=[]
        for direction in range(8):
            idx=direction+(8 if goalie else 0);desc=0x10000+(word(rom,0xed1d+idx*2)&0x7fff)
            frames.append({'descriptor':desc,'flip':bool(word(rom,0xed3d+idx*2)&64)})
            if not goalie:
                h=(word(rom,desc+6)-0x412c)//2
                if not 0<=h<heads_count:raise ValueError('Unsupported preview head geometry')
                head_positions[str(direction)]={'x':signed(heads[heads_base+h])+25,'y':signed(heads[heads_base+heads_count+h])+39,
                  'attr':heads[heads_base+heads_count*3+h],'selector':rom[desc+8]}
        descriptors[goalie]=frames
    def frame(team,goalie,direction):
        info=descriptors[goalie][direction];desc=info['descriptor'];raw,count,base=geometry[goalie]
        part_start=(word(rom,desc)-(0x4168 if goalie else 0x4000))//2
        frame_index=0;cursor=0
        while cursor<part_start and frame_index<raw[0]:cursor+=raw[3+frame_index];frame_index+=1
        if cursor!=part_start or frame_index>=raw[0]:raise ValueError('Invalid preview geometry')
        addr=int.from_bytes(rom[desc+2:desc+5],'little');pos=lorom_offset(addr);size=word(rom,pos)
        top=rom[pos+2:pos+2+size];pos+=2+size;size=word(rom,pos);bottom=rom[pos+2:pos+2+size]
        ptr=word(rom,0xce8a+team*2);detail=rom[lorom_offset(0x980000|ptr):][:32]
        strips=[top,bottom,detail];cache={};pixels=bytearray(48*56)
        for i in reversed(range(raw[3+frame_index])):
            x,y,ti,attr=[raw[base+count*j+part_start+i] for j in range(4)]
            size=16 if attr&16 else 8;adjust=4 if size==16 else 0
            left=signed(x)-adjust+24;up=signed(y)-adjust+40
            for py in range(size):
                for px in range(size):
                    fx=size-1-px if attr&64 else px;fy=size-1-py if attr&128 else py
                    n=ti+fx//8+(fy//8)*16;part=2 if not goalie and n==23 else 1 if n>=16 else 0
                    index=0 if part==2 else n%16;key=(part,index)
                    if key not in cache:cache[key]=tile(strips[part],index)
                    color=cache[key][fy%8][fx%8];xx=left+px;yy=up+py
                    if color and 0<=xx<48 and 0<=yy<56:pixels[yy*48+xx]=color
        return base64.b64encode(pixels).decode('ascii')
    teams=[]
    for team in range(36):
        teams.append({'body':[frame(team,False,d) for d in range(8)],
                      'palettes':[colours(rom,team,False,False),colours(rom,team,False,True),colours(rom,team,True,False),colours(rom,team,True,True)]})
    return {'schema':'issd-editor-preview-local/v1','teams':teams,'goalkeeper':[frame(0,True,d) for d in range(8)],
            'heads':head_positions,'hair_tiles':hair_tiles,
            'flips':{str(int(g)):[f['flip'] for f in descriptors[g]] for g in (False,True)}}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=extract(a.rom.read_bytes());a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    print(f"Prévia local extraída para {len(result['teams'])} equipes e 14 estilos")
