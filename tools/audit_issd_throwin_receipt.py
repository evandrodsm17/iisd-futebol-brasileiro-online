"""Verify captured throw-in contact checks and subsequent ball links."""
import argparse
import hashlib
import json
from pathlib import Path

CASES={'upper-A-Down':(2318,0x1400,20,0), 'lower-B-Right':(2301,0x900,15,8)}


def contact(actor,ball):
    def carry(a,b,center,width):
        total=a+center
        return ((total-b-(0 if total>0xffff else 1))&0xffff)>=width
    return ((actor[2]-ball[2])&0xffff)<0x18 and not carry(actor[0],ball[0],12,24) and not carry(actor[1],ball[1],8,16)


def audit(root):
    results=[]
    for name,(frame,actor,ball_type,linked_type) in CASES.items():
        path=root/name/'receive-hooks.jsonl';raw=path.read_bytes()
        rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        if rows[-1].get('kind')!='done':raise ValueError(f'Incomplete trace: {name}')
        selected=[r for r in rows if r.get('frame')==frame]
        indices=[i for i,r in enumerate(selected) if r.get('d')==actor and r.get('label')=='84E8B0']
        if len(indices)!=1:raise ValueError(f'Expected one contact entry: {name}')
        i=indices[0];entry=selected[i];window=selected[i:i+8]
        labels=[r['label'] for r in window if r.get('d')==actor]
        if labels[:3]!=['84E8B0','84E8BD','84E8E4']:raise ValueError(f'Unexpected contact branch: {name}')
        exit_row=next(r for r in window if r.get('d')==actor and r.get('label')=='84E8E4')
        actor_xyz=[entry['actor_x'],entry['actor_y'],entry['actor_z']]
        ball_xyz=[entry['ball_x'],entry['ball_y'],entry['ball_z']]
        if entry['link_a6']!=0 or entry['ball_type']!=ball_type or entry['actor_field68']!=4 or exit_row['carry']!=0 or not contact(actor_xyz,ball_xyz):
            raise ValueError(f'Contact geometry mismatch: {name}')
        after=next((r for r in selected[i+1:] if r['link_a6']==actor and r['ball_type']==linked_type),None)
        if not after:raise ValueError(f'No later observed ball link: {name}')
        results.append({'case':name,'frame':frame,'actor':actor,'actor_xyz':actor_xyz,'ball_xyz':ball_xyz,
                        'actor_team_field':entry['actor_team'],'ball_type_before':ball_type,'contact_carry':exit_row['carry'],
                        'subsequent_link':after['link_a6'],'subsequent_type':after['ball_type'],
                        'trace_sha256':hashlib.sha256(raw).hexdigest()})
    return {'schema':'issd-throwin-contact-audit/v1','cases':results,
            'limitations':['Two observed contacts do not prove receiver-selection policy or complete possession behavior.',
                           'One replay starts from a synthetic opposite-side coordinate.',
                           'The link is observed in a subsequent callback, not necessarily written at the preceding contact return.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=audit(a.root);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('Validated',len(r['cases']),'contact/link sequences')
