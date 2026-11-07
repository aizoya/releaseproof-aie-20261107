# ReleaseProof event implementation

Keep this repository limited to event-built source. Preserve prior preparation outside it.

- Python 3.12+. Core dependencies: standard library only.
- Verify changes: `python -m unittest discover -s tests -v`.
- With optional ACP dependencies installed: `.venv/bin/python -m unittest discover -s tests -v`.
- Candidates are data interpreted by a strict AST allowlist. Never add `eval`, `exec`, subprocess execution or host filesystem/tool access for candidates.
- Missing, unsupported, stale or inconsistent evidence must block acceptance.
- Do not replace deterministic verdicts with model opinions.
- Keep the local interface loopback-only. External hosting/registration, public publication, billing, credentials, legal acceptance and submission require their own authorized scope.
- Never commit `.env`, agent seeds, tokens, private records, generated database state or large media.
- Clearly label seeded candidates and simulated/offline transport tests. Do not claim sponsor connectivity or general correctness from fixtures.
- OS 2.6 governs; OS 2.7 is not activated.
