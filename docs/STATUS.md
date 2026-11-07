# Local prototype checkpoint — November 7, 2026

## Verified locally

- 43 tests passed with optional uAgents SDK dependencies installed; no skips in that run.
- HTTP path exercised: submit bad repair → acceptance returns conflict; submit correct repair → persisted readback → local acceptance.
- Real SDK schema test: ChatMessage → acknowledgement → evidence response → end-session, using a simulated transport context. No external agent was started. Duplicate deliveries now preserve the same run identity; conflicting message reuse is blocked.
- Meta request preparation and response import tested locally, including truncation/refusal handling and rejecting model instructions to bypass the gate. No authenticated Meta request occurred.
- Candidate file-write attempts refused without creating the canary file.
- Stale-suite, changed-source, changed-candidate and tampered-report acceptance attempts blocked.
- Node syntax check passed. Python compilation passed. Dependency resolver check passed.
- Limited tracked-file hygiene check passed; not a full secret-history scan or vulnerability audit.
- Seeded experiment: 80 trials over four hand-authored candidates and 20 seeds; zero false passes in 60 defective-fixture trials; zero correct rejections in 20 correct-fixture trials. This is not general accuracy evidence.

## Release state

**LOCAL PROTOTYPE — NOT RELEASE READY.** The operating-control declaration intentionally records incomplete public-release controls; the company declaration validator returns BLOCKED. Do not mark missing controls true just to pass it. No public release, external registration, production deployment, paid model calls or competition submission occurred.

## Next concrete work

1. Public repository created after Franklyn explicitly approved publication: https://github.com/aizoya/releaseproof-aie-20261107 . Event-source upload and remote readback are the current publishing step. The earlier local preparation history remains preserved on the build branch and in the saved source bundle. Public source is not a production deployment or competition submission.
2. Establish an approved demo runtime and public ACP submit endpoint. Add rate limiting, request deadlines and persistent storage before exposing it. A read-only Vercel check found earlier project `aizoya-releaseproof-demo` (project ID `prj_GOnohMW76ekvtPyJ0Ar06JzBH5tg`), with an older READY deployment and `releaseproof.aizoya.com` domain entry. This does not establish a working agent endpoint. Nothing there was modified. No editable Replit app matched ReleaseProof.
3. Configure agent identity securely, register on Agentverse and verify ASI:One discovery plus an actual chat round-trip.
4. Verify Meta balance/model/pricing and connect the implemented bounded repair handoff under Franklyn's $20 Meta fallback ceiling. Gemini, MongoDB and Subquadratic access remain separately unverified.
5. Run visual/mobile QA. Record the one-minute actual product demonstration. Prepare submission for Franklyn's approval before the 5 p.m. Pacific deadline.

Full-repository and arbitrary Python repair remain outside this bounded prototype. Do not use it as an execution sandbox for customer code.
