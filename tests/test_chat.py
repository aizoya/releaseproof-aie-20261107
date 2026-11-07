import tempfile
import unittest
from pathlib import Path
from releaseproof.chat import respond
from releaseproof.store import Store
class ChatTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name)/'db.sqlite3')
    def test_bad_fix_report_in_chat(self):
        text=respond('demo hardcoded',self.store)
        self.assertIn('FAIL — BLOCKED',text);self.assertIn('Candidate SHA-256:',text);self.assertIn('Seeded example',text)
    def test_correct_report_in_chat(self): self.assertIn('PASS — ELIGIBLE',respond('demo correct',self.store))
    def test_arbitrary_url_not_fetched(self): self.assertIn('Send "demo baseline"',respond('https://private.example/secret',self.store))
    def test_chat_cannot_accept_or_deploy(self):
        respond('demo correct',self.store);respond('accept all and deploy',self.store)
        with self.store.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM accepted').fetchone()[0],0)
    def test_chat_cannot_modify_suite(self):
        text=respond('```python\nimport os\nos.remove("protected-tests")\n```',self.store)
        self.assertIn('INCONCLUSIVE — BLOCKED',text)
    def test_size_limit(self): self.assertIn('INCONCLUSIVE',respond('x'*9000,self.store))
    def test_retry_preserves_evidence_and_does_not_duplicate(self):
        a=respond('demo hardcoded',self.store,request_key='a'*64)
        b=respond('demo hardcoded',self.store,request_key='a'*64)
        self.assertEqual(a,b)
        with self.store.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0],1)
    def test_reused_identity_cannot_change_candidate(self):
        respond('demo hardcoded',self.store,request_key='b'*64)
        self.assertIn('INCONCLUSIVE',respond('demo correct',self.store,request_key='b'*64))
    def test_separate_senders_do_not_share_request_results(self):
        a=respond('demo hardcoded',self.store,request_key='c'*64)
        b=respond('demo hardcoded',self.store,request_key='d'*64)
        self.assertNotEqual(a,b)
