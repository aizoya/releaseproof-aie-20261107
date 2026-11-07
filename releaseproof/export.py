"""Bounded form parser for replayable HTTP evidence downloads."""
from urllib.parse import parse_qs
from .core import MAX_SOURCE, verify
MAX_EXPORT_BODY=32768

def export_report(raw: bytes) -> dict:
    fields=parse_qs(raw.decode('utf-8'),keep_blank_values=True,strict_parsing=True,
                    errors='strict',max_num_fields=2)
    if set(fields)!={'source','challenge_seed'} or any(len(v)!=1 for v in fields.values()):
        raise ValueError('Invalid export fields.')
    source=fields['source'][0]
    if len(source.encode())>MAX_SOURCE:raise ValueError('Source too large.')
    return verify(source,challenge_seed=fields['challenge_seed'][0])
