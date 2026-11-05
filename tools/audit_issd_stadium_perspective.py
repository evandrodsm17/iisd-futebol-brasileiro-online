"""Estimate four pitch corners when side lines converge in a preview image.

The fitted lines are image measurements, not SNES world or camera coordinates.
"""
import hashlib
from collections import Counter
from PIL import Image
from audit_issd_stadium_projection import is_grass

def measure_perspective(path,crop):
    image=Image.open(path).convert('RGB');width,height=image.size;pixels=image.load()
    def white(c):return c[0]>180 and c[1]>180 and c[2]>160 and abs(c[0]-c[1])<45
    low=max(2,int(crop['y']));high=min(height-2,int(crop['y']+crop['h']));mid=(low+high)//2
    def horizontal(y):
        return sum(white(pixels[x,y]) and is_grass(pixels[x,y-2]) and is_grass(pixels[x,y+2]) for x in range(width//9,2*width//3))
    def peak_center(start,end):
        values={y:horizontal(y) for y in range(start,end)};best=max(values,key=values.get);score=values[best]
        if score<500:raise ValueError('Horizontal lines are not confidently identified')
        adjacent=[y for y in (best-1,best,best+1) if values.get(y,0)>=score*.998]
        return sum(adjacent)/len(adjacent),score
    top,top_score=peak_center(low,mid);bottom,bottom_score=peak_center(mid,high)
    if bottom-top<450:raise ValueError('Unexpected pitch height')
    points=[[],[]]
    for y in range(int(top)+23,int(bottom)-17):
        for x in range(2,width-2):
            if not white(pixels[x,y]):continue
            if not (is_grass(pixels[x-2,y]) or is_grass(pixels[x+2,y]) or is_grass(pixels[x,y-2]) or is_grass(pixels[x,y+2])):continue
            if x<width/3:points[0].append((x,y))
            elif x>width*2/3:points[1].append((x,y))
    def fit(points):
        best=None
        for slope in range(70,131):
            histogram=Counter(x-round(slope*y/100) for x,y in points)
            if not histogram:continue
            offset,votes=histogram.most_common(1)[0]
            if best is None or votes>best[0]:best=(votes,slope/100,offset)
        if best is None or best[0]<300:raise ValueError('Side lines are not confidently identified')
        votes,slope,offset=best;selected=[(x,y) for x,y in points if abs(x-(slope*y+offset))<=2.5]
        if len(selected)<500:raise ValueError('Insufficient side-line samples')
        mean_x=sum(x for x,y in selected)/len(selected);mean_y=sum(y for x,y in selected)/len(selected)
        variance=sum((y-mean_y)**2 for x,y in selected)
        if not variance:raise ValueError('Degenerate side line')
        a=sum((y-mean_y)*(x-mean_x) for x,y in selected)/variance;b=mean_x-a*mean_y
        return a,b,votes,len(selected)
    left=fit(points[0]);right=fit(points[1])
    if abs(left[0]-right[0])<.05:raise ValueError('Perspective difference not established')
    coord=lambda line,y:round(line[0]*y+line[1],3)
    corners={'top_left':[coord(left,top),top],'top_right':[coord(right,top),top],'bottom_left':[coord(left,bottom),bottom],'bottom_right':[coord(right,bottom),bottom]}
    return {'schema':'issd-stadium-pitch-perspective/v1','source':path.as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'image_size':list(image.size),'corners':corners,'evidence':{'method':'horizontal_votes_and_fitted_side_lines','top_white_pixels':top_score,'bottom_white_pixels':bottom_score,'left_votes':left[2],'right_votes':right[2],'left_fit_samples':left[3],'right_fit_samples':right[3]},'limitations':['Corners are estimated from lines in the current static preview; they do not come from the SNES ROM.','A projective transform is an approximation of this image; goal posts and SNES camera remain unverified.']}
