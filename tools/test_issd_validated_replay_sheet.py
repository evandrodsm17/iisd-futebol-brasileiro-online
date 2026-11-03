import tempfile
import unittest
from pathlib import Path
from export_issd_validated_replay_sheet import export


class ValidatedReplaySheetTests(unittest.TestCase):
    def test_rejects_mismatch_before_writing_image(self):
        audit={'frames':[{'script':0xD007,'direction':0,'descriptor':1,
                          'candidate_pixels':10,'nonmatching_pixels':1}]}
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'sheet.png'
            with self.assertRaises(ValueError): export(audit,[],Path(directory),output,0xD007,0)
            self.assertFalse(output.exists())

    def test_rejects_empty_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                export({'frames':[]},[],Path(directory),Path(directory)/'sheet.png',0xD007,0)


if __name__=='__main__': unittest.main()
