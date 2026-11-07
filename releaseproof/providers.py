"""Bounded sponsor calls: seeded inputs only, durable quotas, no automatic retry."""
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .proposals import prepare_meta_request, import_meta_response, MODEL, MAX_RESPONSE
from .core import digest
from .mongo_store import StorageUnavailable

PROVIDERS = {
    'meta': ('https://api.meta.ai/v1/chat/completions', 'MODEL_API_KEY', MODEL),
    'subq': ('https://api.subq.ai/v1/chat/completions', 'SUBQ_API_KEY', 'subq-preview'),
}
MAX_CALLS = 10  # Per provider for this demo version, shared by all warm processes.
META_MAX_REQUEST_BYTES = 8192
SUBQ_MAX_OUTPUT_TOKENS = 512
SUBQ_MAX_REQUEST_BYTES = 8192


class ProviderUnavailable(RuntimeError):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward authorization to another endpoint.


def meta_call_limit():
    """Explicit activation only; call limits do not guarantee a credit/dollar cap."""
    value = os.environ.get('RELEASEPROOF_META_MAX_CALLS', '')
    if (os.environ.get('VERCEL_ENV') != 'preview'
            or not value.isascii() or not value.isdecimal()
            or not 1 <= len(value) <= 2 or not 1 <= int(value) <= MAX_CALLS):
        raise ProviderUnavailable('Meta requires protected Preview and an explicitly approved call limit.')
    return int(value)


def subq_call_limit():
    """Explicit activation only; a call cap is not a dollar or credit cap."""
    value = os.environ.get('RELEASEPROOF_SUBQ_MAX_CALLS', '')
    if (os.environ.get('VERCEL_ENV') != 'preview'
            or not value.isascii() or not value.isdecimal()
            or not 1 <= len(value) <= 2 or not 1 <= int(value) <= MAX_CALLS):
        raise ProviderUnavailable('SubQ requires protected Preview and an explicitly approved call limit.')
    return int(value)


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate response field')
        result[key] = value
    return result


def normalize_subq_candidate(source):
    """Select one explicit Python block; the verifier still checks every expression."""
    if '```' not in source:
        return source, 'none'
    if source.count('```') != 2:
        raise ValueError('Ambiguous candidate blocks')
    match = re.search(r'```python\r?\n(.*?)\r?\n```', source, flags=re.DOTALL)
    if not match or not match.group(1).strip():
        raise ValueError('Unsupported candidate fence')
    return match.group(1), 'single-python-fence'


def enabled_providers():
    enabled = os.environ.get('RELEASEPROOF_LIVE_PROVIDERS', '').split(',')
    available = [name for name, (_, key, _) in PROVIDERS.items()
                 if name in enabled and os.environ.get(key)]
    if 'meta' in available:
        try:
            meta_call_limit()
        except ProviderUnavailable:
            available.remove('meta')
    if 'subq' in available:
        try:
            subq_call_limit()
        except ProviderUnavailable:
            available.remove('subq')
    return available


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


def reserve_call(collection, provider, max_calls=MAX_CALLS):
    for index in range(max_calls):
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
    limit = MAX_CALLS
    if provider == 'meta':
        limit = meta_call_limit()
        examples = Path(__file__).resolve().parents[1] / 'examples'
        seeded = {(examples / (name + '.py')).read_text().strip()
                  for name in ('baseline', 'hardcoded', 'receipt_mismatch')}
        if not isinstance(source, str) or source.strip() not in seeded:
            raise ProviderUnavailable('Meta is restricted to the fixed public seeded fixtures.')
    if provider == 'subq':
        limit = subq_call_limit()
        examples = Path(__file__).resolve().parents[1] / 'examples'
        seeded = {(examples / (name + '.py')).read_text().strip()
                  for name in ('baseline', 'hardcoded', 'receipt_mismatch')}
        if not isinstance(source, str) or source.strip() not in seeded:
            raise ProviderUnavailable('SubQ is restricted to the fixed public seeded fixtures.')
    body = prepare_meta_request(source)
    if provider == 'meta' and len(json.dumps(body, ensure_ascii=True).encode()) > META_MAX_REQUEST_BYTES:
        raise ProviderUnavailable('Meta request exceeds the small demo limit.')
    if provider == 'subq':
        body.update(model=model, store=False, max_tokens=SUBQ_MAX_OUTPUT_TOKENS,
                    reasoning_effort='none')
        del body['max_completion_tokens']
        body['messages'][0]['role'] = 'system'
        if len(json.dumps(body, ensure_ascii=True).encode()) > SUBQ_MAX_REQUEST_BYTES:
            raise ProviderUnavailable('SubQ request exceeds the small demo limit.')
    collection = store.collection.database.get_collection(
        'provider_call_slots_v1', write_concern=store.collection.write_concern)
    slot = None
    try:
        slot = reserve_call(collection, provider, limit)
        raw = (transport or request_bytes)(url, os.environ[key_name], body)
        normalization = 'none'
        model_content_sha256 = None
        # Reuse strict finish/refusal/tool-call/usage validation. Normalize only
        # the expected SubQ model name for the existing Meta-format parser.
        if provider == 'subq':
            if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
                raise ValueError('Oversize response')
            data = json.loads(raw, object_pairs_hook=unique_json_object)
            if data.get('model') != model:
                raise ValueError('Unexpected response model')
            data['model'] = MODEL
            candidate, metadata = import_meta_response(json.dumps(data).encode())
            model_content_sha256 = hashlib.sha256(
                data['choices'][0]['message']['content'].encode()).hexdigest()
            candidate, normalization = normalize_subq_candidate(candidate)
        else:
            if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
                raise ValueError('Oversize response')
            # Refuse ambiguous duplicate fields before the shared import parser.
            json.loads(raw, object_pairs_hook=unique_json_object)
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
        if provider == 'subq':
            receipt.update(candidate_normalization=normalization,
                           model_content_sha256=model_content_sha256)
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
