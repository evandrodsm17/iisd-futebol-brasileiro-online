import unittest
from audit_charge_runtime_snapshot import audit


class SnapshotTests(unittest.TestCase):
    def test_descriptor_overlap(self):
        runs={'runs':[{'samples':[{'descriptor':123}]}]}
        snapshot={'actors':[{'object':'0x0500','descriptor':123,'parts':[{}]},
                            {'object':'0x0600','descriptor':456,'parts':[]}]}
        result=audit(runs,snapshot)
        self.assertEqual(result['actors_examined'],2)
        self.assertEqual(result['matches'],[{'actor':'0x0500','descriptor':123,'direction':None,'parts':1}])


if __name__=='__main__': unittest.main()
