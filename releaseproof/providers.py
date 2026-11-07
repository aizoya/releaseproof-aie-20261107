"""Bounded sponsor calls: seeded inputs only, durable quotas, no automatic retry."""
import hashlib
import json
import os
import time
import uuid
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .proposals import prepare_meta_request, import_meta_response, MODEL, MAX_RESPONSE
from .core import digest
from .mongo_store import StorageUnavailable

PROVIDERS = {
    'meta': ('https://api.meta.ai/v1/chat/completions', 'MODEL_API_KEY', MODEL),
    'subq': ('https://api.subq.ai/v1/chat/completions', 'SUBQ_API_KEY', 'subq-preview'),
}
MAX_CALLS = 10  # Per provider for this demo version, shared by all warm processes.


class ProviderUnavailable(RuntimeError):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward authorization to another endpoint.


def enabled_providers():
    enabled = os.environ.get('RELEASEPROOF_LIVE_PROVIDERS', '').split(',')
    return [name for name, (_, key, _) in PROVIDERS.items()
            if name in enabled and os.environ.get(key)]


def request_bytes(url, key, body):
    request = Request(url, data=json.dumps(body).encode(), method='POST',
                      headers={'Authorization': 'Bearer ' + key,
                               'Content-Type': 'application/json'})
    # No retry: a timeout may still have consumed provider credits.
    with build_opener(NoRedirects()).open(request, timeout=18) as response:
        raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ProviderUnavailable('Provider response exceeds the demo limit.')
        return raw


def reserve_call(collection, provider):
    for index in range(MAX_CALLS):
        slot = f'{provider}:seeded-repair-v1:{index}'
        result = collection.update_one({'_id': slot}, {'$setOnInsert': {
            '_id': slot, 'provider': provider, 'state': 'reserved',
            'reserved_at': time.time(), 'attempt_id': str(uuid.uuid4()),
        }}, upsert=True)
        if result.upserted_id is not None:
            return slot
    raise ProviderUnavailable('Demo call limit reached. No provider request sent.')


def repair(provider, source, store, *, transport=None):
    """Caller supplies a public seeded fixture, never customer/repository context."""
    if provider not in enabled_providers() or store is None:
        raise ProviderUnavailable('Provider or durable development storage is not configured.')
    url, key_name, model = PROVIDERS[provider]
    body = prepare_meta_request(source)
    if provider == 'subq':
        body.update(model=model, store=False, max_tokens=2048)
        del body['max_completion_tokens']
        del body['reasoning_effort']
        body['messages'][0]['role'] = 'system'
    collection = store.collection.database.get_collection(
        'provider_call_slots_v1', write_concern=store.collection.write_concern)
    slot = None
    try:
        slot = reserve_call(collection, provider)
        raw = (transport or request_bytes)(url, os.environ[key_name], body)
        # Reuse strict finish/refusal/tool-call/usage validation. Normalize only
        # the expected SubQ model name for the existing Meta-format parser.
        if provider == 'subq':
            if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
                raise ValueError('Oversize response')
            data = json.loads(raw)
            if data.get('model') != model:
                raise ValueError('Unexpected response model')
            data['model'] = MODEL
            candidate, metadata = import_meta_response(json.dumps(data).encode())
        else:
            candidate, metadata = import_meta_response(raw)
        receipt = {
            'provider': provider, 'model': model,
            'origin': 'server-observed-provider-response',
            'provider_calls': 1, 'response_sha256': hashlib.sha256(raw).hexdigest(),
            'reported_usage': metadata['reported_usage'],
            'usage_verified': False, 'billed_cost_usd': None,
            'input_scope': 'public-seeded-fixture',
            'candidate_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
        }
        report = store.submit(candidate)
        receipt['run_id'] = report['run_id']
        collection.update_one({'_id': slot}, {'$set': {
            'state': 'completed', 'receipt': receipt, 'receipt_sha256': digest(receipt),
        }})
        saved = collection.find_one({'_id': slot})
        if not saved or saved.get('receipt') != receipt or saved.get('receipt_sha256') != digest(receipt):
            raise StorageUnavailable('Provider receipt readback failed.')
        return {'source': candidate, 'report': report, 'proposal': receipt}
    except ProviderUnavailable:
        raise
    except Exception:
        # Never return provider/driver exception text, headers or key material.
        raise ProviderUnavailable('Provider repair could not be verified. No candidate advanced; do not automatically retry.') from None
