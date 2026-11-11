"""Audit observed control-flow after two throw-in ball contacts."""
import argparse
import hashlib
import json
from pathlib import Path

CASES={
 'upper-A-Down':(2318,0x1400,['84C24A','84E8B0','84E8BD','84E8E4','84B9EC','84BA01','84BA6F','84BAA8','84BAB7','84BAFB','83EC1B','85EECE','85F8C5'],0xfff1,0),
 'lower-B-Right':(2301,0x900,['8486E2','84E8B0','84E8BD','84E8E4','84B9F7','84BA01','84BA6F','84BAA8','84BB84','85EECE','85F8C5'],0xffe9,8),
 'lower-A-Left':(2320,0x1500,['84C24A','84E8B0','84E8BD','84E8E4','84B9EC','84BA01','84BA6F','84BAA8','84BB84','85EECE','85F8C5'],0xffee,0),
}


def audit(root):
    cases=[]
    for name,(frame,actor,expected,z,result_type) in CASES.items():
        path=root/name/'receive-hooks.jsonl';raw=path.read_bytes();rows=[json.loads(s) for s in raw.splitlines() if s.strip()]
        if not rows or rows[-1].get('kind')!='done':raise ValueError(f'Incomplete trace: {name}')
        selected=[r for r in rows if r.get('frame')==frame and r.get('d')==actor and r.get('kind')=='exec']
        labels=[r['label'] for r in selected]
        if labels[:len(expected)]!=expected:raise ValueError(f'Unexpected execution path: {name}')
        near=next(r for r in selected if r['label']=='84BAA8')
        if near['ball_z']!=z or near['link_a6']!=0:raise ValueError(f'Unexpected height: {name}')
        if bool((z-0xfff0)&0x8000)!=('84BB84' in expected):raise ValueError(f'Unexpected signed branch: {name}')
        later=next((r for r in rows if r.get('frame')==frame and r.get('link_a6')==actor and r.get('ball_type')==result_type),None)
        if later is None:raise ValueError(f'Missing resulting link/type: {name}')
        cases.append({'case':name,'frame':frame,'actor':actor,'ball_z_word':z,'path':expected,
                      'later_link':actor,'later_ball_type':result_type,'trace_sha256':hashlib.sha256(raw).hexdigest()})
    return {'schema':'issd-throwin-contact-chain/v1','cases':cases,
            'limitations':['Three captured outcomes, including synthetic restarts; no general receiver-selection policy.',
                           'Observed later type does not prove which routine wrote every field.',
                           'Branch test assumes execution has already reached 84:BAA8.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('Validated',len(result['cases']),'contact paths')
