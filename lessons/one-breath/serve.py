"""Loopback-only lesson server. No remote asset requests or publication."""
import argparse,functools,http.server
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);a=p.parse_args()
root=Path(__file__).resolve().parent
class Handler(http.server.SimpleHTTPRequestHandler):
 def end_headers(self):
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
  self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',a.port),functools.partial(Handler,directory=root)).serve_forever()
