"""Measure stadium pitch lines with horizontal and 45-degree pixel votes.

Used only when grass-edge detection fails. Rejects previews without strong,
symmetric parallel lines instead of extrapolating a projection.
"""
import hashlib
from collections import Counter
from PIL import Image
from audit_issd_stadium_projection import is_white,is_grass

def measure_by_lines(path,crop):
    image=Image.open(path).convert('RGB');width,height=image.size;pixels=image.load()
    low=max(2,int(crop['y']));high=min(height-2,int(crop['y']+crop['h']))
    diagonal=Counter()
    for y in range(low,high):
        for x in range(2,width-2):
            if is_white(pixels[x,y]) and (is_grass(pixels[x,y-2]) or is_grass(pixels[x,y+2])):
                diagonal[x-y]+=1
    peaks=[(offset,count) for offset,count in diagonal.items() if count>=200 and count>=diagonal[offset-1] and count>=diagonal[offset+1]]
    candidates=[]
    for left,left_votes in peaks:
        for right,right_votes in peaks:
            if not 1400<=right-left<=2400:continue
            middle=round((left+right)/2)
            middle_votes=max(diagonal[middle-1],diagonal[middle],diagonal[middle+1])
            if middle_votes<200:continue
            candidates.append((left_votes+right_votes+middle_votes,left,right,left_votes,right_votes,middle_votes))
    if not candidates:raise ValueError('White pitch sides are not confidently identified')
    _,left,right,lv,rv,mv=max(candidates)
    def white_between_green(y):
        start=max(2,y+left+60);end=min(width-2,y+right-60)
        return sum(is_white(pixels[x,y]) and is_grass(pixels[x,y-2]) and is_grass(pixels[x,y+2]) for x in range(start,end))
    mid=int(crop['y']+crop['h']/2)
    if not low+10<mid<high-10:raise ValueError('Invalid stadium crop')
    top=max(range(low,mid),key=white_between_green);bottom=max(range(mid,high),key=white_between_green)
    top_votes,bottom_votes=white_between_green(top),white_between_green(bottom)
    if bottom-top<450 or min(top_votes,bottom_votes)<180:raise ValueError('Horizontal lines are not confidently identified')
    return {'schema':'issd-stadium-pitch-projection/v1','source':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':list(image.size),'top_y':top,'bottom_y':bottom,'left_x_minus_y':left,'right_x_minus_y':right,'corners':{'top_left':[top+left,top],'top_right':[top+right,top],'bottom_left':[bottom+left,bottom],'bottom_right':[bottom+right,bottom]},'evidence':{'method':'symmetric_diagonal_and_horizontal_line_votes','top_white_pixels':top_votes,'bottom_white_pixels':bottom_votes,'left_side_white_pixels':lv,'right_side_white_pixels':rv,'center_line_white_pixels':mv},'limitations':['Measures a static exported stadium preview, not the original SNES camera transform.','The detector assumes parallel 45-degree lines and rejects unproven layouts.','Goal posts, height and world-to-SNES scale remain unverified.']}
