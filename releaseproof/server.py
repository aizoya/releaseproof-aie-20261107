"""Loopback-only development server; do not expose as a public agent endpoint."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .core import MAX_SOURCE
from .store import Store, GateBlocked
ROOT = Path(__file__).resolve().parents[1]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Avoid recording request content, paths or query strings.
    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')
    def respond(self, status, body, kind='application/json'):
        if kind == 'application/json': body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if not self.valid_host(): return self.respond(403, {'error': 'Invalid host.'})
        path = urlsplit(self.path).path
        if path == '/health': return self.respond(200, {'status': 'local-ready', 'live_providers': False})
        routes = {'/': ('web/index.html', 'text/html; charset=utf-8'),
                  '/app.js': ('web/app.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('web/style.css', 'text/css; charset=utf-8')}
        if path in routes:
            file, kind = routes[path]
            return self.respond(200, (ROOT / file).read_bytes(), kind)
        if path == '/api/examples':
            return self.respond(200, {p.stem: p.read_text() for p in sorted((ROOT/'examples').glob('*.py'))})
        if path.startswith('/api/runs/'):
            try: return self.respond(200, self.server.store.get(path.rsplit('/', 1)[-1]))
            except (KeyError, GateBlocked): return self.respond(404, {'error': 'Evidence unavailable or invalid.'})
        self.respond(404, {'error': 'Not found.'})
    def do_POST(self):
        if not self.valid_host(): return self.respond(403, {'error': 'Invalid host.'})
        origin = self.headers.get('Origin')
        allowed = (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')
        if origin and origin not in allowed: return self.respond(403, {'error': 'Cross-origin request refused.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'error': 'JSON required.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 20000: return self.respond(413, {'error': 'Request too large or empty.'})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict): raise ValueError('Object required.')
            if self.path == '/api/verify':
                source = body.get('source')
                if not isinstance(source, str) or len(source.encode()) > MAX_SOURCE:
                    raise ValueError('Source must be text of at most 8192 bytes.')
                return self.respond(200, self.server.store.submit(source))
            if self.path == '/api/accept':
                if not all(isinstance(body.get(k), str) for k in ('run_id', 'candidate_sha256')):
                    raise ValueError('Run and candidate identities required.')
                return self.respond(200, self.server.store.accept(body['run_id'], body['candidate_sha256']))
            return self.respond(404, {'error': 'Not found.'})
        except GateBlocked as exc: return self.respond(409, {'error': str(exc), 'gate': 'blocked'})
        except (ValueError, UnicodeError, RecursionError): return self.respond(400, {'error': 'Invalid request.'})

def serve(db_path, port=8765):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.store = Store(db_path)
    print(f'ReleaseProof local preview: http://127.0.0.1:{server.server_port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
