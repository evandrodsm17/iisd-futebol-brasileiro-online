"""Audit scoreboard deltas against goal routine hooks in a focused probe."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(trace,images):
    rows=[json.loads(line) for line in trace.read_bytes().splitlines()]
    cases={r['trial']:r for r in rows if r['type']=='case'}
    frames=collections.defaultdict(list);hooks=collections.defaultdict(list)
    for r in rows:
        if r['type']=='frame': frames[r['trial']].append(r)
        if r['type']=='hook': hooks[r['trial']].append(r)
    if len(cases)!=20 or any(len(frames[i])!=120 for i in range(1,21)):raise ValueError('Incomplete focused probe')
    outcomes=[]
    for i,case in sorted(cases.items()):
        fs=frames[i];initial=[fs[0]['score1'],fs[0]['score2']]
        if initial!=[0,0]: raise ValueError('Initial score unexpected')
        changes=[r for r in fs if [r['score1'],r['score2']]!=initial]
        entries=[r for r in hooks[i] if r['pc']=='86D98C']
        change=changes[0] if changes else None
        prior=[e for e in entries if change and e['step']<=change['step']]
        if change and not prior: raise ValueError(f'Score change without observed hook: {i}')
        entry=prior[-1] if prior else None
        outcomes.append({'trial':i,'side':case['side'],'offset':case['offset'],'height':case['height'],'score_change':None if not change else {'step':change['step'],'before':initial,'after':[change['score1'],change['score2']],'prior_goal_hook':{'step':entry['step'],'native_x':entry['local2a'],'native_y':entry['local2c'],'height_word':entry['z']}}})
    images_checked={}
    for name in ('goal-05-040.png','goal-15-040.png'):
        path=images/name
        if not path.is_file():raise ValueError(f'Missing image {name}')
        images_checked[name]=digest(path)
    return {'schema':'issd-goal-outcome-probe/v1','trace_sha256':digest(trace),'cases':len(cases),'frames':sum(map(len,frames.values())),'scoring_cases':sum(o['score_change'] is not None for o in outcomes),'screenshots_sha256':images_checked,'outcomes':outcomes,'limits':['Synthetic RAM-injected initial states from a single saved game; not naturally played shots.','Score words are sampled after each frame, hooks at instruction entry; equal frame does not establish exact instruction ordering of score write.','Some trajectories did not reach the tested routine; no-score cases do not establish post or crossbar collision.','Images are local to the user and not redistributed; interpretation of labels is visual.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('images',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.trace,a.images);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(f"OK: {result['cases']} cases, {result['frames']} frames, {result['scoring_cases']} score changes with prior hook")
if __name__=='__main__':main()
