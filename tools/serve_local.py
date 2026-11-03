"""Serve the local prototype with the JavaScript module MIME type on Windows."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mjs': 'text/javascript', '.js': 'text/javascript'}

    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=4173)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent/'dist'
    if not root.is_dir():raise SystemExit('Diretório dist não encontrado')
    def handler(*params,**kwargs):return Handler(*params,directory=str(root),**kwargs)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler)
    print(f'Servidor local: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
