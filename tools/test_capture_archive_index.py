import tempfile
import unittest
import zipfile
from pathlib import Path
from audit_capture_archive_index import compare


class ArchiveIndexTests(unittest.TestCase):
    def test_index_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'data.zip';local=root/'index.jsonl'
            local.write_bytes(b'{}\n')
            with zipfile.ZipFile(archive,'w') as z: z.writestr('dir/index.jsonl',b'{}\n')
            self.assertTrue(compare(archive,'index.jsonl',local)['identical'])
            local.write_bytes(b'changed')
            self.assertFalse(compare(archive,'index.jsonl',local)['identical'])
            with zipfile.ZipFile(archive,'a') as z: z.writestr('other/index.jsonl',b'{}\n')
            with self.assertRaises(ValueError): compare(archive,'index.jsonl',local)


if __name__=='__main__': unittest.main()
