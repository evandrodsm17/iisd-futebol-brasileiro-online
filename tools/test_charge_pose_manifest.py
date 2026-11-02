import tempfile
import unittest
from pathlib import Path
from audit_charge_pose_manifest import audit


class PoseManifestTests(unittest.TestCase):
    def test_match_and_missing_file(self):
        runs={'runs':[{'samples':[{'descriptor':0xa749}]}]}
        manifest={'rendered':[{'descriptor':'$A749','filename':'pose.png'},
                              {'descriptor':'invalid'}],'excluded':[]}
        with tempfile.TemporaryDirectory() as directory:
            result=audit(runs,manifest,Path(directory))
            self.assertEqual(result['categories']['rendered']['entries'],2)
            self.assertEqual(len(result['categories']['rendered']['matches']),1)
            self.assertFalse(result['categories']['rendered']['matches'][0]['file_present'])


if __name__=='__main__': unittest.main()
