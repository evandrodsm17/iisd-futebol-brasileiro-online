"""Audit excluded motion/projection pairs against recorded goal and ground events."""
import hashlib
import json
from pathlib import Path

source=json.loads(Path('docs/issd-penalty-motion-projection.json').read_text(encoding='utf8'))
projection=json.loads(Path('dist/data/issd-penalty-projection-samples.json').read_text(encoding='utf8'))
root=Path('analysis/movement-progression-probe')
result=[]
for capture in source['captures']:
    direction=capture['input']; folder=root/f'penalty-projection-{direction}-v3'
    raw=(folder/'mode-hooks.jsonl').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=capture['hooks_sha256']:raise ValueError('Hooks changed')
    events=[json.loads(line) for line in raw.splitlines()]
    graphic=(folder/'graphics.jsonl').read_bytes()
    if hashlib.sha256(graphic).hexdigest()!=capture['graphics_sha256']:raise ValueError('Graphics changed')
    frame_indices={e['frame']:e['delta']-1 for e in map(json.loads,graphic.splitlines()) if e.get('type')=='full_graphics'}
    project=next(c for c in projection['captures'] if c['input']==direction and c['graphics_sha256']==capture['graphics_sha256'])
    found=[]
    for excluded in capture['excluded']:
        tick=excluded['draw_frame']
        def single(site,frame):
            matching=[e for e in events if e.get('site')==site and e.get('frame')==frame and e.get('d')==0x700]
            if len(matching)!=1:raise ValueError(f'Missing or ambiguous {site} at {frame}')
            return matching[0]
        before=single('penalty_shot_step',tick);after=single('penalty_shot_step',tick+1)
        if any(before[k]!=after[k] for k in ('d','side','round')):raise ValueError('Motion context changed')
        coords=project['frames'][frame_indices[excluded['frame']]]
        if not coords or any((after[p]>>8)&255!=coords[k]&255 for p,k in (('px','x'),('py','y'),('pz','height'))):raise ValueError('Draw mismatch')
        state={'x':before['px'],'y':before['py'],'z':before['pz']}
        state.update({name:before[key]|before[key+'_ext']<<16 for name,key in (('vx','dx'),('vy','dy'),('vz','dz'))})
        after_state={'x':after['px'],'y':after['py'],'z':after['pz']}
        after_state.update({name:after[key]|after[key+'_ext']<<16 for name,key in (('vx','dx'),('vy','dy'),('vz','dz'))})
        if excluded['positions_match']:
            goal=single('penalty_increment',tick)
            if after_state['vx']!=0 or after_state['vy']!=0 or goal['side']!=before['side'] or goal['round']!=before['round']:raise ValueError('Unexpected goal transition')
            kind='goal_crossing'
        else:
            ground=single('penalty_ground_contact',tick)
            new_z=(before['pz']+before['dz'])&0xffff
            vz=(state['vz']+32)&0xffffff
            if ground['position_low']!=new_z or ground['velocity']!=(vz&0xffff) or ground['gravity']!=32 or after_state['z']!=(new_z&255) or after_state['vz']!=(-int(vz/2))&0xffffff or state['vx']!=after_state['vx'] or state['vy']!=after_state['vy']:
                raise ValueError('Unexpected bounce transition')
            kind='ground_bounce'
        found.append({'frame':excluded['frame'],'draw_frame':tick,'index':frame_indices[excluded['frame']],
                      'kind':kind,'before':state,'after':after_state,'partX':coords['partX'],'partY':coords['partY'],
                      'size':coords['size'],'oamX':coords['oamX'],'oamY':coords['oamY']})
    if {item['kind'] for item in found}!={'goal_crossing','ground_bounce'}:raise ValueError('Missing cases')
    result.append({'input':direction,'graphics_sha256':capture['graphics_sha256'],'hooks_sha256':capture['hooks_sha256'],'cases':found})
output={'schema':'issd-penalty-motion-exceptions/v1','gravity':32,'captures':result,
        'limits':['Synthetic matches with score and clock interventions; both controls receive directional inputs.',
                  'Goal and velocity changes coincide in the same logged frame; causality is not independently established.',
                  'Bounce is verified only for the captured nonnegative velocity and stopped horizontal motion.',
                  'Upper position bytes were not captured; OAM coordinate bytes only are compared.',
                  'These samples do not establish general goalkeeper or collision behavior.']}
Path('docs/issd-penalty-motion-exceptions.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
Path('dist/data/issd-penalty-motion-exceptions.json').write_text(json.dumps(output,separators=(',',':'))+'\n',encoding='utf8')
print('OK: 2 observed goal transitions and 2 ground bounces')
