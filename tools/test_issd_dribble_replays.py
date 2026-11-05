import json
import tempfile
import unittest
from pathlib import Path
from audit_issd_dribble_replays import audit, signed_delta


class DribbleReplayTest(unittest.TestCase):
    def test_wrapping_and_filters(self):
        self.assertEqual(signed_delta(1,65535),2)
        self.assertEqual(signed_delta(65535,1),-2)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'trace.jsonl'
            row={'input_p2':'Right','link_a6':0x1900,'ball':{'x':1,'y':4,'z':0},'controls':[{}, {'actor':0x1900}],'actors':[{'address':0x1900,'x':65534,'y':0}]}
            airborne={**row,'ball':{**row['ball'],'z':65535}}
            wrong={**row,'link_a6':0}
            path.write_text('\n'.join(map(json.dumps,[row,airborne,wrong])),encoding='utf8')
            result=audit([path])['directions']['Right']
            self.assertEqual(result['samples'],1);self.assertEqual(result['distance_median'],5)


if __name__=='__main__':unittest.main()
