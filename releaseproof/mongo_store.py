"""Optional development evidence persistence. No acceptance, merge or deployment."""
import copy
import os
import threading
import time
import uuid
from .core import digest, verify
from .store import GateBlocked

DATABASE = 'releaseproof_aie_20261107_dev'
COLLECTION = 'application_evidence_v1'
_client = None
_lock = threading.Lock()


class StorageUnavailable(RuntimeError):
    """Public-safe failure; never include driver errors or credentials."""


def configured_store():
    """Lazy shared client, explicitly opt-in; never connect during import."""
    global _client
    if os.environ.get('RELEASEPROOF_STORAGE') != 'mongodb':
        return None
    uri = os.environ.get('MONGODB_URI', '')
    if not uri.startswith('mongodb+srv://'):
        raise StorageUnavailable('MongoDB storage configuration is incomplete.')
    try:
        from pymongo import MongoClient
        from pymongo.write_concern import WriteConcern
        with _lock:
            if _client is None:
                # Low-concurrency demo on a free cluster, one pool per warm
                # Vercel process. These are provisional limits, not load-tested.
                _client = MongoClient(
                    uri, appname='ReleaseProof-development', tls=True,
                    maxPoolSize=3, minPoolSize=0, maxIdleTimeMS=30000,
                    # Bound short writes/readback below the 10s function limit.
                    timeoutMS=2500, serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000, socketTimeoutMS=2500,
                    waitQueueTimeoutMS=1000,
                )
        collection = _client[DATABASE].get_collection(
            COLLECTION, write_concern=WriteConcern(w='majority'))
        return MongoEvidenceStore(collection)
    except Exception:
        raise StorageUnavailable('MongoDB storage is unavailable.') from None


class MongoEvidenceStore:
    def __init__(self, collection):
        self.collection = collection

    def submit(self, source, request_key=None):
        if request_key is not None and (
            not isinstance(request_key, str) or len(request_key) != 64 or
            any(c not in '0123456789abcdef' for c in request_key)
        ):
            raise ValueError('Request key must be an opaque SHA-256 identifier.')
        # Unsupported candidates still produce inconclusive evidence, never execution.
        report = verify(source)
        run_id = request_key if request_key is not None else str(uuid.uuid4())
        fingerprint = digest({'source': source})
        report.update(run_id=run_id, created_at_epoch=time.time(),
                      storage='mongodb', acceptance_enabled=False)
        document = {'_id': run_id, 'source': source, 'fingerprint': fingerprint,
                    'report': report, 'report_sha256': digest(report)}
        try:
            # _id is unique. Concurrent retries converge on one original report.
            # A timed-out upsert is safe to retry with the same request key.
            self.collection.update_one({'_id': run_id}, {'$setOnInsert': document}, upsert=True)
            stored = self.collection.find_one({'_id': run_id})
        except Exception:
            raise StorageUnavailable('Evidence could not be persisted and read back.') from None
        return self._validated(stored, run_id, fingerprint)

    def get(self, run_id):
        if not isinstance(run_id, str) or not 1 <= len(run_id) <= 64:
            raise GateBlocked('Invalid run identifier.')
        try:
            stored = self.collection.find_one({'_id': run_id})
        except Exception:
            raise StorageUnavailable('Evidence could not be read.') from None
        return self._validated(stored, run_id)

    @staticmethod
    def _validated(stored, run_id, fingerprint=None):
        try:
            if not stored or stored['_id'] != run_id:
                raise ValueError()
            if fingerprint is not None and stored['fingerprint'] != fingerprint:
                raise GateBlocked('Conflicting content for a previously processed request.')
            report = stored['report']
            if (stored['fingerprint'] != digest({'source': stored['source']}) or
                digest(report) != stored['report_sha256'] or report['run_id'] != run_id or
                report['storage'] != 'mongodb' or report['acceptance_enabled'] is not False):
                raise ValueError()
            fresh = verify(stored['source'], challenge_seed=report['challenge_seed'])
            # Replay verifies semantics as well as the unkeyed integrity hash.
            # This is still not an immutable or tamper-proof audit service.
            if any(report.get(k) != v for k, v in fresh.items() if k != 'duration_ms'):
                raise ValueError()
            return copy.deepcopy(report)
        except GateBlocked:
            raise
        except Exception:
            raise GateBlocked('Stored evidence failed integrity or replay verification.') from None

    def accept(self, *args, **kwargs):
        raise GateBlocked('Hosted acceptance is disabled.')
