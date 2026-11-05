"""Measure the white pitch lines in an existing stadium preview image.

This measures the exported image, not the original Mode 7 world projection.
It does not identify the goal posts or derive native collision coordinates.
"""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
from PIL import Image

def is_grass(pixel):
    r,g,b=pixel[:3];return g>75 and g>r*1.05 and g>b*1.05

def is_white(pixel):
    r,g,b=pixel[:3];return r>145 and g>160 and b>125 and abs(r-g)<60

def measure(path):
    image=Image.open(path).convert('RGB')
    if image.width<2000 or image.height<800:raise ValueError('Unexpected layout image dimensions')
    pixels=image.load();rows=[]
    for y in range(image.height):
        run=None;spans=[]
        for x in range(image.width):
            green=is_grass(pixels[x,y])
            if green and run is None:run=x
            if not green and run is not None:
                if x-run>=1000:spans.append((run,x-1))
                run=None
        if run is not None and image.width-run>=1000:spans.append((run,image.width-1))
        if spans:rows.append((y,*max(spans,key=lambda s:s[1]-s[0])))
    if not rows:raise ValueError('Pitch grass not detected')
    first,last=rows[0],rows[-1]
    if last[0]-first[0]<500:raise ValueError('Unexpected grass area')
    # In this preview the unbroken grass boundary is a 45-degree line.
    left=Counter(x-y for y,x,_ in rows);right=Counter(x-y for y,_,x in rows)
    left_offset,left_votes=left.most_common(1)[0];right_offset,right_votes=right.most_common(1)[0]
    if left_votes<400 or right_votes<400:raise ValueError('Grass edges not consistently diagonal')
    def white_score(y):
        lo=max(0,y+left_offset+200);hi=min(image.width,y+right_offset-200)
        return sum(is_white(pixels[x,y]) for x in range(lo,hi))
    top=max(range(first[0],min(first[0]+150,last[0])),key=white_score)
    bottom=max(range(max(first[0],last[0]-149),last[0]+1),key=white_score)
    top_votes,bottom_votes=white_score(top),white_score(bottom)
    if min(top_votes,bottom_votes)<300:raise ValueError('Horizontal white lines not detected')
    def side_votes(offset,left_side):
        return sum(0<=y+(left_offset+offset if left_side else right_offset-offset)<image.width and is_white(pixels[y+(left_offset+offset if left_side else right_offset-offset),y]) for y in range(top+20,bottom-20))
    left_inset=max(range(0,320),key=lambda n:side_votes(n,True))
    right_inset=max(range(0,320),key=lambda n:side_votes(n,False))
    left_white=left_offset+left_inset;right_white=right_offset-right_inset
    if min(side_votes(left_inset,True),side_votes(right_inset,False))<200:raise ValueError('Diagonal white lines not detected')
    return {'schema':'issd-stadium-pitch-projection/v1','source':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':list(image.size),'top_y':top,'bottom_y':bottom,'left_x_minus_y':left_white,'right_x_minus_y':right_white,'corners':{'top_left':[top+left_white,top],'top_right':[top+right_white,top],'bottom_left':[bottom+left_white,bottom],'bottom_right':[bottom+right_white,bottom]},'evidence':{'top_white_pixels':top_votes,'bottom_white_pixels':bottom_votes,'left_side_white_pixels':side_votes(left_inset,True),'right_side_white_pixels':side_votes(right_inset,False)},'limitations':['Measures the static exported stadium preview, not the original SNES camera transform.','Pixel colors and antialiasing can affect detection; line width is not modeled.','Goal posts, height and world-to-SNES scale remain unverified.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=measure(a.image);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('OK:',result['corners'])
