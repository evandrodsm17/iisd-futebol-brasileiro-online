"""Join audited OAM projections to native motion hooks without distributing raw traces."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

reports = [json.loads(Path(f'docs/issd-penalty-{name}-projection.json').read_text(encoding='utf8')) for name in ('directional','intermediate-ball','large-ball')]
root=Path('analysis/movement-progression-probe')
result=[]
for index in range(2):
    group=[r['captures'][index] for r in reports]
    if len({c['graphics_sha256'] for c in group}) != 1 or len({c['name'] for c in group}) != 1:
        raise ValueError('Capture mismatch')
    folder=root/group[0]['name']
    graphics=(folder/'graphics.jsonl').read_bytes()
    if hashlib.sha256(graphics).hexdigest()!=group[0]['graphics_sha256']:
        raise ValueError('Graphics hash mismatch')
    frames={e['frame']:e['delta']-1 for e in map(json.loads,graphics.splitlines()) if e.get('type')=='full_graphics'}
    hook_raw=(folder/'mode-hooks.jsonl').read_bytes()
    hooks=defaultdict(list)
    for e in map(json.loads,hook_raw.splitlines()):
        if e.get('site')=='penalty_shot_step' and e.get('d')==0x700:hooks[e['frame']].append(e)
    samples=[None]*40
    excluded=[]
    for capture,size in zip(group,(8,8,16)):
        for observed in capture['samples']:
            matches=[c for c in observed['candidates'] if c['lag']==2 and c['matches_both']]
            if len(matches)!=1:raise ValueError('Ambiguous projection')
            c=matches[0]; before=hooks[c['draw_frame']];after=hooks[c['draw_frame']+1]
            if len(before)!=1 or len(after)!=1:raise ValueError('Ambiguous motion hook')
            before,after=before[0],after[0]
            if any(((after[p]>>8)&255)!=(c[name]&255) for p,name in (('px','object_x'),('py','object_y'),('pz','object_height'))):
                raise ValueError('Hook and drawing object diverge')
            pos=all(after[p]==(before[p]+before[v])&0xffff for p,v in (('px','dx'),('py','dy'),('pz','dz')))
            horiz=all(before[v]==after[v] and before[v+'_ext']==after[v+'_ext'] for v in ('dx','dy'))
            vertical=((before['dz']|(before['dz_ext']<<16))+32)&0xffffff == (after['dz']|(after['dz_ext']<<16))
            frame=frames[observed['frame']]
            if not(pos and horiz and vertical):
                excluded.append({'frame':observed['frame'],'draw_frame':c['draw_frame'],'positions_match':pos,'horizontal_velocity_match':horiz,'gravity_match':vertical})
                continue
            state={'x':before['px'],'y':before['py'],'z':before['pz']}
            state.update({name:before[key]|(before[key+'_ext']<<16) for name,key in (('vx','dx'),('vy','dy'),('vz','dz'))})
            samples[frame]={'before':state,'partX':c['offset_x'],'partY':c['offset_y'],'size':size,'oamX':c['oam_x'],'oamY':c['oam_y']}
    if sum(s is not None for s in samples)!=37 or len(excluded)!=2:raise ValueError('Unexpected sample counts')
    result.append({'input':group[0]['input_direction'],'graphics_sha256':group[0]['graphics_sha256'],
                   'hooks_sha256':hashlib.sha256(hook_raw).hexdigest(),'samples':samples,'excluded':excluded})
output={'schema':'issd-penalty-motion-projection/v1','gravity':32,'captures':result,
        'limits':['Synthetic score and clock; both controllers receive the direction.',
                  'The hook at draw_frame+1 matches the sampled drawing object; this does not establish universal timing.',
                  'Upper position bytes were not captured by the hook; only projected OAM bytes are compared.',
                  'Four non-free-flight pairs are excluded; their cause is not assumed.',
                  'ROM, raw hooks and screenshots remain local.']}
Path('docs/issd-penalty-motion-projection.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-motion-projection.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 74 projected free-flight samples; 4 differing pairs excluded')
