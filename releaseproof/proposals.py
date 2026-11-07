"""Meta request preparation / response import. This module makes no network calls."""
import hashlib
import json
import re
from .core import CONTRACT, MAX_SOURCE, parse_candidate

MODEL = 'muse-spark-1.3'
ENDPOINT = 'https://api.meta.ai/v1/chat/completions'
MAX_RESPONSE = 65536
class ProposalError(ValueError): pass

def prepare_meta_request(source: str) -> dict:
    # Only the bounded language is sent in a prepared request. No verifier source,
    # challenge seed/cases, database state, credentials or customer records.
    parse_candidate(source)
    return {
        'model': MODEL, 'stream': False, 'max_completion_tokens': 2048,
        'reasoning_effort': 'low',
        'messages': [
            {'role':'developer','content':
             'Repair the supplied synthetic quote and receipt functions. Return only Python code, '
             'with both exact signatures and one return expression per function. Allowed: integer '
             'arithmetic (+,-,*), parameters, comparisons and conditionals. No calls, imports, files, '
             'loops, annotations or decorators. Do not include an approval verdict or change tests.'},
            {'role':'user','content': json.dumps({'contract': CONTRACT, 'candidate': source})},
        ],
    }

def import_meta_response(raw: bytes) -> tuple[str, dict]:
    if not isinstance(raw, bytes) or len(raw)>MAX_RESPONSE:
        raise ProposalError('Response exceeds the 64 KiB import limit.')
    try:
        data=json.loads(raw)
        if not isinstance(data,dict): raise ValueError()
        if data.get('model') != MODEL: raise ValueError()
        choices=data['choices']
        if not isinstance(choices,list) or len(choices)!=1: raise ValueError()
        choice=choices[0]
        if choice.get('finish_reason')!='stop':
            raise ProposalError('Incomplete, refused or tool-calling response cannot become a candidate.')
        message=choice['message']
        if message.get('role')!='assistant' or message.get('tool_calls') or message.get('refusal'):
            raise ValueError()
        source=message['content']
        if not isinstance(source,str): raise ValueError()
        fenced=re.fullmatch(r'\s*```(?:python)?\s*\n(.*?)\n```\s*',source,flags=re.DOTALL)
        if fenced: source=fenced.group(1)
        if not source.strip() or len(source.encode())>MAX_SOURCE: raise ValueError()
        # Candidate may be unsupported or wrong: verification decides, not import.
        usage=data.get('usage',{})
        if not isinstance(usage,dict): raise ValueError()
        safe_usage={}
        for k in ('prompt_tokens','completion_tokens','total_tokens'):
            if k in usage:
                if type(usage[k]) is not int or not 0<=usage[k]<=10000000: raise ValueError()
                safe_usage[k]=usage[k]
    except ProposalError: raise
    except (KeyError,TypeError,ValueError,UnicodeError,RecursionError) as exc:
        raise ProposalError('Response is not a supported complete Meta Chat Completions result.') from exc
    return source, {
        'provider':'meta', 'model':MODEL, 'origin':'imported-response-unverified',
        'authenticity_verified':False, 'response_sha256':hashlib.sha256(raw).hexdigest(),
        'reported_usage':safe_usage, 'usage_verified':False,
    }
