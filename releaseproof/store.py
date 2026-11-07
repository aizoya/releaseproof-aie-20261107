"""Local evidence and an enforced acceptance gate. Not a tamper-proof audit service."""
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from .core import digest, suite_digest, verify

class GateBlocked(ValueError):
    pass

class Store:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, report TEXT NOT NULL,
                report_hash TEXT NOT NULL, created REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS accepted (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1), run_id TEXT NOT NULL,
                candidate_hash TEXT NOT NULL, accepted REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS requests (
                request_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, run_id TEXT NOT NULL);
            ''')
    def connect(self):
        return sqlite3.connect(self.path, timeout=5)
    def submit(self, source: str, provenance: dict | None = None, request_key: str | None = None) -> dict:
        if request_key is not None and (not isinstance(request_key,str) or len(request_key)!=64 or
                                       any(c not in '0123456789abcdef' for c in request_key)):
            raise ValueError('Request key must be an opaque SHA-256 identifier.')
        if provenance is not None:
            allowed = {'provider','model','origin','authenticity_verified','response_sha256','reported_usage','usage_verified'}
            if not isinstance(provenance,dict) or set(provenance) != allowed:
                raise ValueError('Unsupported provenance fields.')
            if (provenance['provider'] != 'meta' or provenance['model'] != 'muse-spark-1.3' or
                provenance['origin'] != 'imported-response-unverified' or
                provenance['authenticity_verified'] is not False or provenance['usage_verified'] is not False or
                not isinstance(provenance['response_sha256'],str) or
                len(provenance['response_sha256']) != 64 or
                any(c not in '0123456789abcdef' for c in provenance['response_sha256'])):
                raise ValueError('Invalid unverified response provenance.')
            usage = provenance['reported_usage']
            if (not isinstance(usage,dict) or set(usage)-{'prompt_tokens','completion_tokens','total_tokens'} or
                any(type(v) is not int or not 0<=v<=10000000 for v in usage.values())):
                raise ValueError('Invalid reported usage.')
        report = verify(source)
        if provenance is not None:
            report['provenance'] = provenance
        report['run_id'] = str(uuid.uuid4())
        report['created_at_epoch'] = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_key is not None:
                fingerprint=digest({'source':source,'provenance':provenance})
                previous=db.execute('SELECT fingerprint,run_id FROM requests WHERE request_key=?',(request_key,)).fetchone()
                if previous is not None:
                    if previous[0]!=fingerprint:
                        raise GateBlocked('Conflicting content for a previously processed request.')
                    return self.get(previous[1])
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?)',
                       (report['run_id'], source, json.dumps(report), digest(report), report['created_at_epoch']))
            if request_key is not None:
                db.execute('INSERT INTO requests VALUES (?,?,?)',(request_key,fingerprint,report['run_id']))
        return report
    def get(self, run_id: str) -> dict:
        with self.connect() as db:
            row = db.execute('SELECT source,report,report_hash FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None: raise KeyError('Unknown run.')
        source, raw, expected = row
        report = json.loads(raw)
        if digest(report) != expected or hashlib.sha256(source.encode()).hexdigest() != report['candidate_sha256']:
            raise GateBlocked('Stored evidence integrity check failed.')
        return report
    def accept(self, run_id: str, candidate_sha256: str) -> dict:
        # Transaction prevents evidence changes between read, fresh verification and acceptance.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT source,report,report_hash FROM runs WHERE id=?', (run_id,)).fetchone()
            if row is None: raise GateBlocked('Unknown verification run.')
            source, raw, evidence_hash = row
            report = json.loads(raw)
            if digest(report) != evidence_hash:
                raise GateBlocked('Stored evidence integrity check failed.')
            if report['candidate_sha256'] != candidate_sha256 or report['suite_sha256'] != suite_digest():
                raise GateBlocked('Candidate or verification suite changed; verify again.')
            fresh = verify(source, challenge_seed=report['challenge_seed'])
            if (report['status'] != 'pass' or fresh['status'] != 'pass' or
                fresh['candidate_sha256'] != candidate_sha256):
                raise GateBlocked('Only a freshly verified passing candidate may advance.')
            db.execute('INSERT OR REPLACE INTO accepted VALUES (1,?,?,?)',
                       (run_id, candidate_sha256, time.time()))
        return {'state': 'accepted-locally', 'run_id': run_id, 'candidate_sha256': candidate_sha256,
                'deployed': False, 'merged': False}
