"""Join observed penalty scores to the same captured ball scenes."""
import hashlib
import json
from pathlib import Path

motion=json.loads(Path('docs/issd-penalty-motion-exceptions.json').read_text(encoding='utf8'))
result=[]
for capture in motion['captures']:
    folder=Path('analysis/movement-progression-probe')/f"penalty-projection-{capture['input']}-v3"
    raw=(folder/'mode-hooks.jsonl').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=capture['hooks_sha256']:raise ValueError('Hooks changed')
    events=[json.loads(line) for line in raw.splitlines()]
    goal_case=next(c for c in capture['cases'] if c['kind']=='goal_crossing')
    shots=[e for e in events if e.get('site')=='penalty_shot_final' and e['frame']<=goal_case['draw_frame']]
    if len(shots)!=3:raise ValueError('Expected three launches')
    records=[];previous=[0,0]
    for i,shot in enumerate(shots):
        upper=shots[i+1]['frame'] if i+1<len(shots) else goal_case['draw_frame']+1
        results=[e for e in events if e.get('site')=='penalty_crossing_resolved' and shot['frame']<e['frame']<upper and all(e[k]==shot[k] for k in ('d','side','round'))]
        if len(results)!=1:raise ValueError('Ambiguous shot result')
        e=results[0];score=[e['penalty_home'],e['penalty_away']];team=shot['side']//2
        difference=[score[n]-previous[n] for n in range(2)]
        if difference not in ([0,0],[int(team==0),int(team==1)]):raise ValueError('Unexpected score change')
        increments=[x for x in events if x.get('site')=='penalty_increment' and x['frame']==e['frame'] and x['side']==shot['side'] and x['round']==shot['round']]
        scored=any(difference)
        if len(increments)!=(1 if scored else 0):raise ValueError('Increment does not match score')
        record={'launch_frame':shot['frame'],'resolved_frame':e['frame'],'side':shot['side'],'round':shot['round'],
                'input_word':shot['input_word'],'launch_flags':shot['flags'],'resolution_flags':e['shot_flags'],
                'position':{'x':e['x_coord'],'y':e['y_coord'],'height':e['height']},
                'scored':scored,'score':score,'route':'direct' if increments else 'observed_no_goal'}
        records.append(record);previous=score
    if records[-1]['resolved_frame']!=goal_case['draw_frame'] or not records[-1]['scored']:raise ValueError('Goal scene mismatch')
    result.append({'input':capture['input'],'graphics_sha256':capture['graphics_sha256'],'hooks_sha256':capture['hooks_sha256'],
                   'goal_frame_index':goal_case['index'],'shots':records})
output={'schema':'issd-penalty-scene-score/v1','captures':result,
        'limits':['Synthetic scores and clocks; directional commands sent to both controllers.',
                  'The no-goal result is observed; its collision or goalkeeper cause is not inferred.',
                  'Score display aligned with ball scene candidate; captured HUD timing is not validated.',
                  'Only three shots from each recorded sequence are reproduced.']}
Path('docs/issd-penalty-scene-score.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-scene-score.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 6 observed shots connected to their own captured scene')
