"""Correlate native sound-queue calls with edge and scoring hooks."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

def audit(path):
 raw=path.read_bytes();records=[json.loads(line) for line in raw.splitlines()]
 cases={r['trial']:r for r in records if r['type']=='case'}
 frames=collections.Counter(r['trial'] for r in records if r['type']=='frame')
 if len(cases)!=96 or any(frames[i]!=32 for i in range(1,97)):raise ValueError('Incomplete capture')
 hooks=[r for r in records if r['type']=='hook']
 edge={(r['trial'],r['step']) for r in hooks if r['pc']=='838BF8'}
 goal={(r['trial'],r['step']) for r in hooks if r['pc']=='86D98C'}
 calls=[r for r in hooks if r['pc']=='80BF05']
 goal_codes=collections.Counter(r['regA']&255 for r in calls if (r['trial'],r['step']) in goal)
 edge_codes=collections.Counter(r['regA']&255 for r in calls if any((r['trial'],r['step']-dt) in edge for dt in range(5)))
 effects=collections.Counter(r['regA'] for r in hooks if r['pc']=='83A000')
 if len(edge)!=30 or len(goal)!=12 or goal_codes!={9:12,76:12} or edge_codes or effects!={9:6}:raise ValueError('Unexpected observations')
 return {'schema':'issd-goal-audio-queue-probe/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':len(cases),'frames':sum(frames.values()),'edge_events':len(edge),'goal_events':len(goal),'sound_queue_codes_on_goal_frame':dict(sorted(goal_codes.items())),'sound_queue_codes_within_edge_and_four_frames':dict(sorted(edge_codes.items())),'effect_dispatch_arguments':dict(sorted(effects.items())),'limits':['Sound queue code is a command, not a recording of audible PCM or proof of a specific sound.','Same frame does not prove causality; the disassembly separately shows goal-path calls with codes 09 and 4C.','One synthetic initial state and a four-frame observation window do not rule out later or other impact sounds.','83A000 forwards to A49AF2; its argument is an effect selector and has not been established as audio.','The edge events were offscreen under this setup; conditions for some commands were not met.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args();result=audit(a.trace);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',result['goal_events'],'goal frames;',result['edge_events'],'edge events;',result['sound_queue_codes_within_edge_and_four_frames'],'queue calls near edge')
if __name__=='__main__':main()
