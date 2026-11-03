"""Map observed draw-list stack ranges to candidate SNES OAM slots."""
import argparse
import hashlib
import json
from pathlib import Path


def slots(before, after, stack_origin=0x03df):
    if not all(isinstance(v, int) for v in (before, after)):
        raise ValueError('Missing stack values')
    if before > stack_origin or after > before or after < 0x01df:
        raise ValueError('Stack range outside expected low OAM buffer')
    if (stack_origin-before) % 4 or (before-after) % 4:
        raise ValueError('Stack range is not aligned to four-byte OAM entries')
    return list(range((stack_origin-before)//4, (stack_origin-after)//4))


def summarize(rows, actor):
    events = [r for r in rows if r.get('type') == 'draw_entry']
    found = []
    for i, event in enumerate(events):
        if event.get('object') != actor: continue
        if i+1 >= len(events) or events[i+1]['step'] != event['step']:
            found.append({'step': event['step'], 'frame': event['frame'], 'status': 'missing-next-entry'})
            continue
        try:
            candidate = slots(event['stack'], events[i+1]['stack'])
        except ValueError as exc:
            found.append({'step': event['step'], 'frame': event['frame'], 'status': str(exc)})
            continue
        found.append({'step': event['step'], 'frame': event['frame'], 'list_y': event['list_y'],
                      'stack_before': event['stack'], 'stack_after': events[i+1]['stack'],
                      'candidate_slots': candidate, 'status': 'observed-stack-range'})
    return {'actor': actor, 'entries': found,
            'limitations': ['Slot mapping assumes the observed 03DF stack-origin path and four pushed bytes per part.',
                            'No draw callback in a frame does not imply the object was invisible.',
                            'Other object types may share or modify the OAM buffer; verify pixels and timing.',
                            'Frame numbers are callback times; compare with frame-end buffers separately.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace',type=Path)
    p.add_argument('--actor',type=lambda s:int(s,0),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); raw=a.trace.read_bytes()
    result=summarize([json.loads(line) for line in raw.splitlines() if line.strip()],a.actor)
    result.update({'schema':'issd-draw-trace/v1', 'source':{'path':a.trace.as_posix(),
                   'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('actor entries:',len(result['entries']))


if __name__=='__main__': main()
