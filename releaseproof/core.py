"""A bounded Python-expression verifier. Never eval/exec candidate source."""
from __future__ import annotations
import ast
import hashlib
import json
import random
import secrets
import time
from dataclasses import asdict, dataclass

PARAMS = ('subtotal_cents', 'delivery_cents', 'discount_cents')
FUNCTIONS = ('quote_total', 'receipt_total')
MAX_SOURCE = 8192
MAX_NODES = 256
MAX_VALUE = 10**12
CONTRACT = {
    'version': 'quote-v1',
    'formula': 'subtotal_cents - discount_cents + delivery_cents',
    'domain': 'integer cents; subtotal 0..1000000; delivery 0..100000; discount 0..subtotal',
    'receipt': 'receipt_total must equal quote_total and the independent expected total',
    'scope': 'two pure Python functions, each with exactly one return expression',
}
# These synthetic cases are transparent and reproducible, not a hidden benchmark.
CASES = (
    ('visible-example', 12500, 500, 0),
    ('different-subtotal', 14000, 500, 0),
    ('no-delivery', 12500, 0, 0),
    ('discount', 12500, 500, 1500),
    ('cent-precision', 9999, 199, 1),
    ('zero-order', 0, 0, 0),
    ('fully-discounted', 2500, 700, 2500),
    ('upper-bound', 1000000, 100000, 0),
)
ENGINE_VERSION = 'bounded-ast-v1'
CHALLENGE_COUNT = 32

class Unsupported(ValueError):
    """Candidate is outside the permitted language; do not execute it."""


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def suite_digest() -> str:
    return digest({'contract': CONTRACT, 'cases': CASES, 'engine': ENGINE_VERSION,
                   'challenge_policy': 'random-v1:32:subtotal0..1000000:delivery0..100000:discount0..subtotal'})


def challenge_cases(seed: int):
    rng = random.Random(seed)
    for i in range(CHALLENGE_COUNT):
        subtotal = rng.randint(0, 1000000)
        delivery = rng.randint(0, 100000)
        discount = rng.randint(0, subtotal)
        yield (f'challenge-{i + 1:02d}', subtotal, delivery, discount)


def parse_candidate(source: str) -> dict[str, ast.expr]:
    if not isinstance(source, str) or len(source.encode()) > MAX_SOURCE:
        raise Unsupported('Source must be text of at most 8192 bytes.')
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise Unsupported('Candidate is not supported Python syntax.') from exc
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise Unsupported('Candidate exceeds the expression complexity limit.')
    functions = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in FUNCTIONS:
            raise Unsupported('Only quote_total and receipt_total functions are permitted.')
        args = node.args
        if (node.name in functions or node.decorator_list or node.returns or
            node.type_comment or node.type_params or args.posonlyargs or
            args.kwonlyargs or args.vararg or args.kwarg or args.defaults or
            args.kw_defaults or tuple(a.arg for a in args.args) != PARAMS or
            any(a.annotation or a.type_comment for a in args.args)):
            raise Unsupported('Function signatures must match the frozen contract.')
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Return) or node.body[0].value is None:
            raise Unsupported('Each function must contain exactly one return expression.')
        expression = node.body[0].value
        validate_expression(expression)
        functions[node.name] = expression
    if set(functions) != set(FUNCTIONS):
        raise Unsupported('Both quote_total and receipt_total are required.')
    return functions


def validate_expression(node: ast.AST, depth: int = 0) -> None:
    if depth > 24:
        raise Unsupported('Expression nesting exceeds limit.')
    if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= MAX_VALUE:
        return
    if isinstance(node, ast.Name) and node.id in PARAMS:
        return
    if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult):
        children = (node.left, node.right)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.USub, ast.UAdd):
        children = (node.operand,)
    elif isinstance(node, ast.IfExp):
        children = (node.test, node.body, node.orelse)
    elif (isinstance(node, ast.Compare) and len(node.ops) == 1 and
          type(node.ops[0]) in (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
        children = (node.left, node.comparators[0])
    else:
        raise Unsupported('Unsupported operation: calls, imports, files, attributes, loops and external access are refused.')
    for child in children:
        validate_expression(child, depth + 1)


def evaluate(node: ast.expr, values: dict[str, int]) -> int | bool:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return values[node.id]
    if isinstance(node, ast.IfExp):
        result = evaluate(node.body if evaluate(node.test, values) else node.orelse, values)
    elif isinstance(node, ast.UnaryOp):
        value = evaluate(node.operand, values)
        result = -value if isinstance(node.op, ast.USub) else value
    elif isinstance(node, ast.BinOp):
        left, right = evaluate(node.left, values), evaluate(node.right, values)
        if type(left) is not int or type(right) is not int:
            raise Unsupported('Arithmetic requires integer values.')
        if isinstance(node.op, ast.Add): result = left + right
        elif isinstance(node.op, ast.Sub): result = left - right
        else: result = left * right
    elif isinstance(node, ast.Compare):
        left, right = evaluate(node.left, values), evaluate(node.comparators[0], values)
        operators = {ast.Eq: lambda: left == right, ast.NotEq: lambda: left != right,
                     ast.Lt: lambda: left < right, ast.LtE: lambda: left <= right,
                     ast.Gt: lambda: left > right, ast.GtE: lambda: left >= right}
        return operators[type(node.ops[0])]()
    else:
        raise Unsupported('Unsupported expression.')
    if type(result) not in (int, bool) or abs(result) > MAX_VALUE:
        raise Unsupported('Evaluation exceeded the bounded integer range.')
    return result


@dataclass(frozen=True)
class Check:
    name: str
    inputs: dict[str, int]
    expected_cents: int
    quote_cents: int | bool
    receipt_cents: int | bool
    passed: bool


def verify(source: str, challenge_seed: int | None = None) -> dict:
    start = time.perf_counter()
    if challenge_seed is None:
        challenge_seed = secrets.randbits(64)
    if type(challenge_seed) is not int or not 0 <= challenge_seed < 2**64:
        raise ValueError('Challenge seed must be an unsigned 64-bit integer.')
    report = {
        'schema_version': 1, 'engine': ENGINE_VERSION,
        'candidate_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'suite_sha256': suite_digest(), 'contract': CONTRACT,
        'status': 'inconclusive', 'gate': 'blocked', 'checks': [],
        'reason': '', 'scope': 'Synthetic fixture; restricted expression evaluation; no general Python execution.',
        'provider_calls': 0,
        'challenge_seed': challenge_seed,
    }
    try:
        functions = parse_candidate(source)
        cases = (*CASES, *challenge_cases(challenge_seed))
        for name, subtotal, delivery, discount in cases:
            inputs = dict(zip(PARAMS, (subtotal, delivery, discount)))
            expected = subtotal - discount + delivery
            quote = evaluate(functions['quote_total'], inputs)
            receipt = evaluate(functions['receipt_total'], inputs)
            passed = type(quote) is int and type(receipt) is int and quote == receipt == expected
            report['checks'].append(asdict(Check(name, inputs, expected, quote, receipt, passed)))
        failures = sum(not c['passed'] for c in report['checks'])
        report['status'] = 'fail' if failures else 'pass'
        report['gate'] = 'blocked' if failures else 'eligible'
        report['reason'] = f'{failures} of {len(cases)} checks failed.' if failures else 'All 8 fixture and 32 fresh challenge checks passed; eligible for explicit local acceptance.'
    except (Unsupported, RecursionError) as exc:
        report['reason'] = str(exc) if isinstance(exc, Unsupported) else 'Expression exceeds safe parser limits.'
    report['duration_ms'] = round((time.perf_counter() - start) * 1000, 3)
    report['checks_run'] = len(report['checks'])
    return report
