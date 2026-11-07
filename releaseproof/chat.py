"""Deterministic chat boundary shared by the CLI and optional ACP transport."""
import json
import re
from pathlib import Path
from .core import MAX_SOURCE
from .store import Store, GateBlocked

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'
HELP = ('ReleaseProof verifies a synthetic quote/receipt contract using restricted Python expressions. '
        'Send "demo baseline", "demo hardcoded", "demo receipt_mismatch", or "demo correct". '
        'Alternatively send both functions in one fenced Python code block. '
        'Amounts are integer cents: subtotal - discount + delivery. '
        'No repository access, deployment or acceptance is available through chat.')

def respond(text: str, store: Store, request_key: str | None = None) -> str:
    if not isinstance(text, str) or len(text.encode()) > MAX_SOURCE + 128:
        return 'INCONCLUSIVE — request too large or not text. No candidate advanced.'
    command = text.strip().lower()
    if command in {f'demo {name}' for name in ('baseline','hardcoded','receipt_mismatch','correct')}:
        source = (EXAMPLES / f'{command.split()[1]}.py').read_text()
        provenance = 'Seeded example selected by the user; not a live AI-generated repair.'
    else:
        match = re.fullmatch(r'\s*```(?:python)?\s*\n(.*?)\n```\s*', text, flags=re.DOTALL)
        if not match: return HELP
        source = match.group(1)
        provenance = 'User-supplied candidate; authorization and origin are not independently established.'
    try:
        report = store.submit(source,request_key=request_key)
    except GateBlocked:
        return 'INCONCLUSIVE — conflicting or invalid prior request evidence. No candidate advanced.'
    failed = [c for c in report['checks'] if not c['passed']]
    lines = [f"{report['status'].upper()} — {report['gate'].upper()}", report['reason'], provenance,
             f"Run: {report['run_id']}", f"Candidate SHA-256: {report['candidate_sha256']}",
             f"Suite SHA-256: {report['suite_sha256']}", f"Replay seed: {report['challenge_seed']}"]
    for check in (failed[:3] or report['checks'][:1]):
        lines.append(f"{check['name']}: expected {check['expected_cents']} cents; quote {check['quote_cents']}; receipt {check['receipt_cents']}.")
    lines.append('40 bounded checks are not proof of general correctness. No merge or deployment. Live model calls: 0.')
    return '\n'.join(lines)
