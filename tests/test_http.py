import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from releaseproof.server import Handler
from releaseproof.store import Store
from test_verifier import example
class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.store=Store(Path(self.tmp.name)/'db.sqlite3')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        h={'Content-Type':'application/json'};h.update(headers or {})
        c.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body),h)
        r=c.getresponse();raw=r.read();status=r.status;kind=r.getheader('Content-Type');c.close()
        return status,json.loads(raw) if kind=='application/json' else raw
    def test_assets(self):
        for path in ('/','/app.js','/style.css','/api/examples','/health'): self.assertEqual(self.request(path)[0],200)
    def test_end_to_end(self):
        _,bad=self.request('/api/verify',{'source':example('hardcoded')});self.assertEqual(self.request('/api/accept',bad)[0],409)
        _,good=self.request('/api/verify',{'source':example('correct')});self.assertEqual(self.request('/api/runs/'+good['run_id'])[1],good)
        s,a=self.request('/api/accept',good);self.assertEqual((s,a['state']),(200,'accepted-locally'))
    def test_origin_and_host(self):
        self.assertEqual(self.request('/api/verify',{'source':example('correct')},{'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/health',headers={'Host':'evil.example'})[0],403)
    def test_invalid_requests(self):
        self.assertEqual(self.request('/api/verify',{'source':None})[0],400)
        self.assertEqual(self.request('/api/verify',{'source':'x'*8193})[0],400)
        self.assertEqual(self.request('/api/verify',{'source':'x'*30000})[0],413)
    def test_html_remains_data(self):
        _,r=self.request('/api/verify',{'source':'<script>alert(1)</script>'});self.assertEqual((r['status'],r['gate']),('inconclusive','blocked'))
