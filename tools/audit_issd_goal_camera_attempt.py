"""Audit camera warm-up attempt without inferring visible collision."""
import argparse,collections,hashlib,json
from pathlib import Path

def audit(path,image):
 raw=path.read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
 cases={r['trial']:r for r in rows if r['type']=='case'}
 frames=collections.Counter(r['trial'] for r in rows if r['type']=='frame')
 if len(cases)!=4 or any(frames[i]!=40 for i in range(1,5)):raise ValueError('Incomplete capture')
 edge=[r for r in rows if r.get('pc')=='838BF8']
 if not edge:raise ValueError('No edge events')
 events={(r['trial'],r['step']) for r in edge}
 sounds=[r for r in rows if r.get('pc')=='80BF05' and any((r['trial'],r['step']-d) in events for d in range(5))]
 screenshot=image.read_bytes()
 return {'schema':'issd-goal-camera-attempt/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'screenshot_sha256':hashlib.sha256(screenshot).hexdigest(),'cases':len(cases),'frames':sum(frames.values()),'warmup_frames_per_case':150,'edge_hook_entries':len(edge),'edge_cases':len({r['trial'] for r in edge}),'edge_screen_x_range':[min(r['x'] for r in edge),max(r['x'] for r in edge)],'edge_screen_y_range':[min(r['y'] for r in edge),max(r['y'] for r in edge)],'audio_queue_calls_same_or_four_following_frames':len(sounds),'limitations':['Coordinates are values in $0408/$040C, and the selected screenshot must be inspected for actual visibility.','Warm-up did not visibly position the camera at the tested right goal.','Repeated hook entries do not establish separate physical impacts.','Sound queue calls are not PCM recordings; this setup does not exclude audio in other conditions.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('image',type=Path);p.add_argument('output',type=Path);a=p.parse_args();result=audit(a.trace,a.image);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',result['edge_hook_entries'],'edge hooks in',result['edge_cases'],'cases; x:',result['edge_screen_x_range'])
if __name__=='__main__':main()
