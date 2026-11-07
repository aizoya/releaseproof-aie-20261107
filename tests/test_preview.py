import io
import json
import unittest
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator
from releaseproof.preview import app
from test_verifier import example
class PreviewTests(unittest.TestCase):
    def call(self,path='/',body=None,origin=None,overrides=None):
        env={};setup_testing_defaults(env)
        env.update({'PATH_INFO':path,'QUERY_STRING':'','HTTP_HOST':'preview.example','wsgi.url_scheme':'https'})
        if body is not None:
            raw=json.dumps(body).encode();env.update({'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)})
        if origin is not None:env['HTTP_ORIGIN']=origin
        env.update(overrides or {})
        result={}
        def start(status,headers,exc_info=None):result.update(status=int(status.split()[0]),headers=dict(headers))
        iterator=validator(app)(env,start)
        try:raw=b''.join(iterator)
        finally:iterator.close()
        return result['status'],json.loads(raw) if result['headers']['Content-Type']=='application/json' else raw,result['headers']
    def test_real_verification_without_storage(self):
        for name,status in [('baseline','fail'),('hardcoded','fail'),('correct','pass')]:
            s,r,_=self.call('/api/verify',{'source':example(name)})
            self.assertEqual((s,r['status']),(200,status));self.assertEqual(r['storage'],'not-persisted');self.assertFalse(r['acceptance_enabled'])
    def test_passing_result_cannot_enable_acceptance(self):
        _,r,_=self.call('/api/verify',{'source':example('correct')})
        s,a,_=self.call('/api/accept',r)
        self.assertEqual((s,a['gate']),(503,'blocked'))
    def test_no_database_or_provider_used(self):
        with patch('sqlite3.connect',side_effect=AssertionError('Unexpected database access')):
            self.assertEqual(self.call('/api/verify',{'source':example('correct')})[0],200)
    def test_capability_config_is_explicit(self):
        s,c,_=self.call('/api/config');self.assertEqual(s,200)
        self.assertEqual((c['mode'],c['persistent_evidence'],c['acceptance_enabled'],c['live_providers']),('hosted-preview',False,False,False))
    def test_assets_and_examples(self):
        for path in ('/','/app.js','/style.css','/api/examples','/health'):
            s,_,h=self.call(path);self.assertEqual(s,200);self.assertEqual(h['Cache-Control'],'no-store')
    def test_private_file_paths_never_served(self):
        for path in ('/.env','/releaseproof/store.py','/../README.md','/api/runs/123'):
            self.assertIn(self.call(path)[0],(404,503))
    def test_cross_origin_refused(self):
        self.assertEqual(self.call('/api/verify',{'source':example('correct')},origin='https://evil.example')[0],403)
        self.assertEqual(self.call('/api/verify',{'source':example('correct')},origin='https://preview.example')[0],200)
    def test_invalid_oversize_missing_and_extra_fields(self):
        for body in ({'source':None},{'source':'x'*8193},{'source':example('correct'),'approve':True}):self.assertEqual(self.call('/api/verify',body)[0],400)
        self.assertEqual(self.call('/api/verify',{'source':'x'*30000})[0],413)
        self.assertEqual(self.call('/api/verify',{})[0],400)
    def test_no_invented_run_on_unsupported_code(self):
        _,r,_=self.call('/api/verify',{'source':'import os'})
        self.assertEqual((r['status'],r['gate']),('inconclusive','blocked'));self.assertNotIn('run_id',r)

    def test_http_export_replays_exact_original_seed(self):
        from urllib.parse import urlencode
        from releaseproof.core import verify
        original=verify(example('correct'),challenge_seed=2**64-1)
        raw=urlencode({'source':example('correct'),'challenge_seed':original['challenge_seed']}).encode()
        status,report,headers=self.call('/api/report',overrides={'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)})
        self.assertEqual(status,200)
        self.assertIn('attachment; filename="releaseproof-',headers['Content-Disposition'])
        self.assertEqual(report['challenge_seed'],str(2**64-1))
        self.assertEqual(report['checks'],original['checks'])
        self.assertFalse(report['acceptance_enabled'])
    def test_export_rejects_conflicting_fields_and_invalid_seeds(self):
        from urllib.parse import urlencode
        for fields in [{'source':example('correct'),'challenge_seed':str(2**64)}, {'source':example('correct'),'challenge_seed':'-1'}, {'source':example('correct'),'challenge_seed':'1.2'}]:
            raw=urlencode(fields).encode()
            self.assertEqual(self.call('/api/report',overrides={'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)})[0],400)
    def test_export_cannot_approve_a_failed_candidate(self):
        from urllib.parse import urlencode
        raw=urlencode({'source':example('hardcoded'),'challenge_seed':'42'}).encode()
        _,report,_=self.call('/api/report',overrides={'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw)})
        self.assertEqual((report['status'],report['gate']),('fail','blocked'))

class DeploymentLayoutTests(unittest.TestCase):
    def test_file_based_entrypoint_and_route_are_consistent(self):
        from pathlib import Path
        from importlib.util import spec_from_file_location, module_from_spec
        root=Path(__file__).resolve().parents[1]
        config=json.loads((root/'vercel.json').read_text())
        self.assertIn('api/index.py',config['functions'])
        self.assertEqual(config['rewrites'],[{'source':'/(.*)','destination':'/api/index'}])
        spec=spec_from_file_location('preview_entry',root/'api/index.py');module=module_from_spec(spec);spec.loader.exec_module(module)
        self.assertIs(module.app,app)
