import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from releaseproof.core import verify
from releaseproof.store import Store, GateBlocked
ROOT=Path(__file__).resolve().parents[1]
def example(name): return (ROOT/'examples'/f'{name}.py').read_text()

class VerifierTests(unittest.TestCase):
    def test_original_defect_reproduced(self):
        r=verify(example('baseline'));v=r['checks'][0]
        self.assertEqual((v['quote_cents'],v['expected_cents']),(12500,13000))
        self.assertEqual(r['gate'],'blocked')
    def test_hardcoded_fix_cannot_game_checks(self):
        r=verify(example('hardcoded'))
        self.assertTrue(r['checks'][0]['passed']);self.assertEqual(r['status'],'fail')
    def test_receipt_mismatch(self):
        r=verify(example('receipt_mismatch'));c=r['checks'][0]
        self.assertEqual(c['quote_cents'],c['expected_cents']);self.assertNotEqual(c['receipt_cents'],c['expected_cents'])
        self.assertEqual(r['status'],'fail')
    def test_correct_candidate(self):
        r=verify(example('correct'))
        self.assertEqual((r['status'],r['gate'],r['checks_run']),('pass','eligible',40))
    def test_fresh_challenges_catch_visible_fixture_overfitting(self):
        source=example('correct').replace('return subtotal_cents - discount_cents + delivery_cents',
            'return subtotal_cents - discount_cents + delivery_cents if subtotal_cents <= 14000 else 1100000')
        r=verify(source,challenge_seed=42)
        self.assertTrue(all(c['passed'] for c in r['checks'][:8]))
        self.assertEqual(r['status'],'fail')
        self.assertTrue(any(not c['passed'] for c in r['checks'][8:]))
    def test_seed_reproduces_challenge_evidence(self):
        a=verify(example('correct'),challenge_seed=42)
        b=verify(example('correct'),challenge_seed=42)
        self.assertEqual(a['checks'],b['checks'])
        c=verify(example('correct'),challenge_seed=43)
        self.assertNotEqual(a['checks'],c['checks'])
    def test_file_write_never_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'canary';r=verify(example('correct')+f'\nopen({str(p)!r},"w").write("modified")')
            self.assertFalse(p.exists());self.assertEqual((r['status'],r['gate']),('inconclusive','blocked'))
    def test_unsupported_programs_fail_closed(self):
        expr='return subtotal_cents - discount_cents + delivery_cents'
        programs=['import os\n'+example('correct'),'@print\n'+example('correct'),'def broken(',example('correct')*2]
        programs += [example('correct').replace(expr,p) for p in ['return __import__("os").getcwd()','return 1.0','return 2 ** 1000000000','while True: pass','return [1] * 100000000']]
        for p in programs:
            with self.subTest(source=p[:50]): self.assertEqual((verify(p)['status'],verify(p)['gate']),('inconclusive','blocked'))
    def test_oversize_refused(self): self.assertEqual(verify('x'*8193)['status'],'inconclusive')
    def test_boolean_not_integer_cents(self):
        p=example('correct').replace('return subtotal_cents - discount_cents + delivery_cents','return subtotal_cents == 0')
        self.assertEqual(verify(p)['status'],'fail')
    def test_overflow_inconclusive(self):
        p=example('correct').replace('return subtotal_cents - discount_cents + delivery_cents','return subtotal_cents * 1000000000000')
        self.assertEqual(verify(p)['status'],'inconclusive')
    def test_conditionals(self):
        p=example('correct').replace('return subtotal_cents - discount_cents + delivery_cents','return subtotal_cents + delivery_cents if discount_cents == 0 else subtotal_cents - discount_cents + delivery_cents')
        self.assertEqual(verify(p)['status'],'pass')

class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name)/'db.sqlite3')
    def test_failed_candidate_cannot_advance(self):
        r=self.store.submit(example('hardcoded'))
        with self.assertRaises(GateBlocked): self.store.accept(r['run_id'],r['candidate_sha256'])
        with self.store.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM accepted').fetchone()[0],0)
    def test_missing_evidence(self):
        with self.assertRaises(GateBlocked): self.store.accept('missing','0'*64)
    def test_acceptance_readback(self):
        r=self.store.submit(example('correct'));self.assertEqual(self.store.get(r['run_id']),r)
        a=self.store.accept(r['run_id'],r['candidate_sha256'])
        self.assertEqual(a['state'],'accepted-locally');self.assertFalse(a['merged']);self.assertFalse(a['deployed'])
    def test_changed_identity(self):
        r=self.store.submit(example('correct'))
        with self.assertRaises(GateBlocked): self.store.accept(r['run_id'],'0'*64)
    def test_changed_source(self):
        r=self.store.submit(example('correct'))
        with self.store.connect() as db: db.execute('UPDATE runs SET source=? WHERE id=?',(example('baseline'),r['run_id']))
        with self.assertRaises(GateBlocked): self.store.accept(r['run_id'],r['candidate_sha256'])
    def test_tampered_evidence(self):
        r=self.store.submit(example('hardcoded'))
        with self.store.connect() as db: db.execute('UPDATE runs SET report=? WHERE id=?',(json.dumps({**r,'status':'pass'}),r['run_id']))
        with self.assertRaises(GateBlocked): self.store.get(r['run_id'])
        with self.assertRaises(GateBlocked): self.store.accept(r['run_id'],r['candidate_sha256'])
    def test_changed_suite(self):
        r=self.store.submit(example('correct'))
        with patch('releaseproof.store.suite_digest',return_value='changed'):
            with self.assertRaises(GateBlocked): self.store.accept(r['run_id'],r['candidate_sha256'])
    def test_retry_single_acceptance(self):
        r=self.store.submit(example('correct'))
        for _ in range(2): self.store.accept(r['run_id'],r['candidate_sha256'])
        with self.store.connect() as db: self.assertEqual(db.execute('SELECT count(*) FROM accepted').fetchone()[0],1)
