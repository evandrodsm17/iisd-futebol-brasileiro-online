import json
from pathlib import Path

outcomes = json.loads(Path('docs/issd-penalty-native-outcomes.json').read_text(encoding='utf8'))
waits = json.loads(Path('docs/issd-penalty-deferred-checks.json').read_text(encoding='utf8'))
contacts = json.loads(Path('docs/issd-penalty-contact-chain.json').read_text(encoding='utf8'))
for shot in outcomes['cases']:
    if shot['reason'] == 'deferred':
        wait = next(w for w in waits['cases'] if w['resolved_frame'] == shot['resolved_frame'])
        contact = next(c for c in contacts['cases'] if c['action_frame'] == wait['action_frame'])
        shot['deferred'] = {'selectedAt': contact['selected_frame'], 'actionAt': contact['action_frame'],
            'flags': contact['result_flags'], 'checks': [{'tick': c['frame'], 'flags': c['flags'], 'snapshot': c['snapshot']} for c in wait['checks']]}
Path('dist/data/issd-penalty-replay.json').write_text(json.dumps({'schema': 'issd-penalty-replay/v1', 'cases': outcomes['cases']}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf8')
