# AIZOYA ReleaseProof

**An independent acceptance gate for a bounded software-repair task.**

Event-built prototype for the AIE Code Summit, November 7, 2026. Primary theme: **Trust but Verify**. This is a local working prototype, not a deployed service or completed submission.

## Run in two commands

Requires Python 3.12 or newer. The core and local web interface have no third-party runtime dependencies. Run from this source checkout (web assets and fixtures are checkout-relative):

```sh
python -m unittest discover -s tests -v
python -m releaseproof serve
```

Open **http://127.0.0.1:8765** on the same computer. The preview is loopback-only, so a phone or Cloud Browser on another computer cannot reach it. Do not expose this development server publicly. It has not undergone visual browser QA.

Choose **Original defect**, then **Convincing fix**, then **Correct formula**. Verify each. The convincing fix returns $130 for every order; it passes the visible example and fails other checks. Local acceptance re-verifies the exact stored candidate against the same recorded challenge seed. Failed or inconclusive candidates cannot advance. Acceptance changes only a local record; it does not merge, deploy, publish or submit anything.

## What is implemented

- A frozen synthetic contract: `subtotal_cents - discount_cents + delivery_cents`.
- Independent quote and receipt comparison using integer cents.
- Eight public fixture cases plus 32 fresh challenge cases per run; replay seed and identities retained in evidence.
- Candidate SHA-256, suite identity, actual inputs/outputs, elapsed time, pass/fail/inconclusive, and an enforced local acceptance gate.
- SQLite evidence and revalidation on acceptance. This is a local fallback, **not MongoDB integration**.
- A mobile-responsive local page, CLI, deterministic chat handler, and optional uAgents Agent Chat Protocol adapter.

## Execution boundary

**No candidate source is run with Python `exec`, `eval`, a shell or a subprocess.** The verifier parses and interprets only two pure functions, `quote_total` and `receipt_total`, each with the three exact contract parameters and one return expression. Allowed expressions: bounded integers, parameters, addition, subtraction, multiplication, comparisons, unary signs and conditionals. Imports, calls, attributes, files, assignments, loops and decorators are refused.

This prevents candidates in the accepted language from writing verifier files. It is **not an operating-system sandbox** and does not support arbitrary repositories, Python packages, untrusted dependencies or multi-file repairs. The host's OS-sandbox probe failed; no OS-isolation claim is made. Unsupported or resource-limited candidates yield **inconclusive + blocked**, never pass. The same-process trusted verifier remains modifiable by a host administrator; hashes are identity/tamper checks, not access controls or signed audit evidence.

Passing 40 checks is not a proof of correctness over all inputs. Fixtures are seeded examples, not evidence that a live model generated these failures. Fresh challenge cases reduce simple fixture overfitting but are not a secret formal specification.

## CLI and evidence

```sh
python -m releaseproof verify examples/hardcoded.py
python -m releaseproof verify examples/correct.py
python -m releaseproof show RUN_ID
python -m releaseproof accept RUN_ID CANDIDATE_SHA256
```

Verify exits `0` for pass, `1` for fail and `2` for inconclusive. Acceptance is explicit and local. SQLite state is ignored by Git under `.state/`. Report IDs and exact source digest must match; stale-suite, modified-source or tampered-evidence attempts are blocked. Repeated acceptance replaces a single local accepted-state record.

## Fetch integration

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements-agent.lock
.venv/bin/python -m unittest discover -s tests -v
```

The adapter uses uAgents 0.26.1 and uagents-core 0.4.12; the dependency snapshot is in `requirements-agent.lock`. Its request/acknowledgement/response path was tested offline with actual SDK schemas and a simulated transport context. Core-only runs skip the two SDK tests when the dependency is absent. No live Agentverse or ASI:One test has passed yet.

Chat requests: `demo baseline`, `demo hardcoded`, `demo receipt_mismatch`, `demo correct`, or a fenced Python candidate. Unknown requests return scope/help. The adapter never fetches URLs or attachments, runs models, accepts candidates, or deploys code. It does not maintain conversation history. Duplicate chat deliveries reuse the same evidence when sender, message ID and content match. Conflicting reuse is refused. Public deployment still needs rate limits, request deadlines and operational controls.

Launching externally requires **separately approved hosting and registration**, a securely configured agent seed, a public HTTPS submit endpoint and verified Agentverse setup. No secrets belong in chat or Git. The local website URL is not an ACP endpoint. After those gates, the operator can run `python -m releaseproof.agent --connect`; without `--connect`, it refuses startup. No seed or key has been created here. Registration success and ASI:One discovery must be independently observed.

Official references:
- https://docs.agentverse.ai/documentation/launch-agents/agentverse-sdk/u-agents
- https://uagents.fetch.ai/docs/examples/asi-1

## Hosted verification preview (prepared, not deployed)

A separate WSGI entrypoint (`app.py`) and `vercel.json` prepare a stateless preview for Vercel. It runs the real bounded checks and supports report downloads, but persists no server evidence and always blocks acceptance. The local server retains its SQLite acceptance gate. No live hosting deployment has been verified. See [docs/HOSTING_PLAN.md](docs/HOSTING_PLAN.md) for the target, credit snapshot, cost gate and missing connections.

## Meta repair handoff

The CLI prepares a bounded request for Meta’s documented `muse-spark-1.3` Chat Completions API, then independently verifies an imported response:

```sh
python -m releaseproof prepare-meta examples/baseline.py
python -m releaseproof import-meta path/to/response.json
```

These commands make **no network calls**. They do not create a key, consume credits or establish that Meta generated a supplied response. Imported provenance remains explicitly unverified; token counts are reported, not authenticated. Incomplete responses, tool calls, refusals, unsupported model IDs and malformed payloads are refused. A complete response may still fail or be inconclusive after independent verification. No model-provided approval controls the gate. Challenge cases and seeds are excluded from prepared model requests.

Live execution still requires a securely configured Meta key, verified access/current pricing and enforceable usage controls within the authorized $20 fallback. Never put a key in these JSON files or Git. Official reference: https://dev.meta.ai/docs/protocols/chat-completions .

## Sponsor integration status

| Provider | Status |
|---|---|
| Fetch | Adapter coded; actual SDK schema test passed offline; live registration/discovery pending |
| Meta | Request preparation and response-import adapter tested locally; no authenticated live calls |
| Gemini | Planned independent challenger; event account/model access unverified |
| MongoDB | Planned evidence backend; currently local SQLite |
| Subquadratic | Planned history-aware check selection; not connected |
| Analytics / CMS | Not implemented; not needed for this acceptance-gate slice |

Do not claim sponsor usage from provider mentions or preparation accounts. No provider credits were consumed by this increment. Dependency downloads are separate from API use.

## Reproducible seeded experiment

```sh
python scripts/benchmark.py
```

`docs/seeded-benchmark.json` records four hand-authored candidates × 20 seeds = 80 trials. These are repeated synthetic fixtures, **not 80 independent software tasks**, a customer pilot, competitor comparison or model-quality result. It includes denominators, verdicts, seeds, candidate/suite hashes and local timings. No broad accuracy or 10x claim is supported. No ARR or traction claims are made by this implementation.

## Repository and event provenance

See [docs/PROVENANCE.md](docs/PROVENANCE.md). This source was created from scratch after Franklyn authorized coding on November 7. Earlier product planning, illustrative PDFs, video and preparation website are separate and were not copied into this repository. AI assistance: OpenAI Codex wrote and tested this implementation under Franklyn's direction. The existing SDK is an external dependency; the protocol adapter follows the official example's message structure. No customer code or data is included.

The public event-source repository is https://github.com/aizoya/releaseproof-aie-20261107 . Franklyn explicitly approved its creation and source upload. Public source does not establish a working deployment. Before operational release: complete the full secret/history and dependency audit; verify actual sponsor connections; perform mobile/browser QA; complete live endpoint and ASI:One tests; record a new **one-minute working-product demo with voiceover**. Submission remains a separate approval. No competition submission has been made.
