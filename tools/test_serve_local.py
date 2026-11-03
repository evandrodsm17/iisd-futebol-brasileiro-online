import functools
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen
from serve_local import Handler


class LocalServerTest(unittest.TestCase):
    def test_module_mime_and_content(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'probe.mjs').write_text('export const ok = true;',encoding='utf8')
            server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=folder))
            worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/probe.mjs') as response:
                    self.assertEqual(response.headers.get_content_type(),'text/javascript')
                    self.assertEqual(response.headers.get('Cache-Control'),'no-cache')
                    self.assertEqual(response.read(),b'export const ok = true;')
            finally:
                server.shutdown();server.server_close();worker.join()


if __name__=='__main__':unittest.main()
