"""Behavioral tests with simulated storage, not an Atlas network integration."""
import copy
import os
import unittest
from unittest.mock import patch
from releaseproof.core import digest
from releaseproof.mongo_store import MongoEvidenceStore, StorageUnavailable, configured_store
from releaseproof.store import GateBlocked
from test_verifier import example


class Collection:
    def __init__(self):
        self.documents = {}
        self.fail_write = self.fail_read = False
        self.lose_response = False
    def update_one(self, query, update, upsert):
        if self.fail_write: raise RuntimeError('private-driver-message')
        self.documents.setdefault(query['_id'], copy.deepcopy(update['$setOnInsert']))
        if self.lose_response: raise TimeoutError('private-driver-message')
    def find_one(self, query):
        if self.fail_read: raise RuntimeError('private-driver-message')
        return copy.deepcopy(self.documents.get(query['_id']))


class MongoStoreTests(unittest.TestCase):
    def setUp(self):
        self.collection = Collection()
        self.store = MongoEvidenceStore(self.collection)
        self.key = 'a' * 64
    def test_persist_replay_and_block_bad_candidate(self):
        for fixture, status in [('correct', 'pass'), ('hardcoded', 'fail')]:
            report = self.store.submit(example(fixture))
            self.assertEqual(report['status'], status)
            self.assertEqual(report, self.store.get(report['run_id']))
            self.assertFalse(report['acceptance_enabled'])
            with self.assertRaises(GateBlocked): self.store.accept(report['run_id'])
    def test_retries_reuse_original_report_and_reject_conflicting_content(self):
        first = self.store.submit(example('correct'), self.key)
        self.assertEqual(first, self.store.submit(example('correct'), self.key))
        with self.assertRaises(GateBlocked): self.store.submit(example('hardcoded'), self.key)
        self.assertEqual(len(self.collection.documents), 1)
    def test_uncertain_write_retry_recovers_original_evidence(self):
        self.collection.lose_response = True
        with self.assertRaises(StorageUnavailable): self.store.submit(example('correct'), self.key)
        first = copy.deepcopy(self.collection.documents[self.key]['report'])
        self.collection.lose_response = False
        self.assertEqual(first, self.store.submit(example('correct'), self.key))
    def test_write_and_read_errors_do_not_return_passing_evidence_or_secrets(self):
        for attr in ('fail_write', 'fail_read'):
            setattr(self.collection, attr, True)
            with self.assertRaises(StorageUnavailable) as ctx: self.store.submit(example('correct'))
            self.assertNotIn('private-driver-message', str(ctx.exception))
            setattr(self.collection, attr, False)
    def test_corruption_and_rehashed_false_pass_are_blocked(self):
        for rehash in (False, True):
            report = self.store.submit(example('hardcoded'))
            doc = self.collection.documents[report['run_id']]
            doc['report']['status'] = 'pass'
            if rehash: doc['report_sha256'] = digest(doc['report'])
            with self.assertRaises(GateBlocked): self.store.get(report['run_id'])
    def test_unknown_run_and_invalid_keys(self):
        with self.assertRaises(GateBlocked): self.store.get('unknown')
        for key in ('', 'x'*64, {'$ne': None}):
            with self.assertRaises(ValueError): self.store.submit(example('correct'), key)
    def test_storage_is_opt_in_and_missing_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True): self.assertIsNone(configured_store())
        with patch.dict(os.environ, {'RELEASEPROOF_STORAGE':'mongodb'}, clear=True):
            with self.assertRaises(StorageUnavailable): configured_store()

    def test_real_driver_accepts_configuration_and_client_is_reused(self):
        try:
            from pymongo import MongoClient
        except ImportError:
            self.skipTest('Optional PyMongo dependency is not installed.')
        import releaseproof.mongo_store as module
        clients = []
        def make_client(uri, **options):
            # Validate real driver options without DNS, credentials or network.
            client = MongoClient('mongodb://127.0.0.1:1', connect=False, **options)
            clients.append(client)
            return client
        try:
            with patch.dict(os.environ, {'RELEASEPROOF_STORAGE':'mongodb','MONGODB_URI':'mongodb+srv://placeholder.invalid'}, clear=True), patch.object(module, '_client', None), patch('pymongo.MongoClient', side_effect=make_client):
                a = configured_store(); b = configured_store()
                self.assertEqual(len(clients), 1)
                self.assertIs(a.collection.database.client, b.collection.database.client)
                self.assertEqual(a.collection.write_concern.document, {'w':'majority'})
                self.assertEqual(clients[0].options.pool_options.max_pool_size, 3)
        finally:
            for client in clients: client.close()
