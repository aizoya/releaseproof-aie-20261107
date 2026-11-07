# Local prototype checkpoint — November 7, 2026

## Verified locally

- Combined MongoDB adapter and interface correction: 65 Python tests passed with optional uAgents SDK and PyMongo dependencies installed; no skips in this run. Five JavaScript response-timing regression tests also passed. Node syntax and Git whitespace checks passed.
- HTTP path exercised: submit bad repair → acceptance returns conflict; submit correct repair → persisted readback → local acceptance.
- Real SDK schema test: ChatMessage → acknowledgement → evidence response → end-session, using a simulated transport context. No external agent was started. Duplicate deliveries now preserve the same run identity; conflicting message reuse is blocked.
- Meta request preparation and response import tested locally, including truncation/refusal handling and rejecting model instructions to bypass the gate. No authenticated Meta request occurred.
- Candidate file-write attempts refused without creating the canary file.
- Stale-suite, changed-source, changed-candidate and tampered-report acceptance attempts blocked.
- Node syntax check passed. Python compilation passed. Dependency resolver check passed.
- Limited tracked-file hygiene check passed; not a full secret-history scan or vulnerability audit.
- Seeded experiment: 80 trials over four hand-authored candidates and 20 seeds; zero false passes in 60 defective-fixture trials; zero correct rejections in 20 correct-fixture trials. This is not general accuracy evidence.

## Release state

**BOUNDED PROTOTYPE WITH A PROTECTED PREVIEW — NOT RELEASE READY.** The operating-control declaration intentionally records incomplete public-release controls; the recorded company declaration validation is BLOCKED. Do not mark missing controls true just to pass it. Public event-source publication and a protected preview were previously authorized and observed. No production promotion, external agent registration, paid model call or competition submission is established.

## Current integration checkpoint

- The stale-response fix from `fix/ui-verification-race` is integrated on `build/hosted-preview` at `84ba8fe`. Both MongoDB readiness notes and mobile QA notes were retained when resolving the README merge conflict.
- The MongoDB adapter is opt-in and locally tested, including uncertain-write recovery, readback/replay, conflicting retries and corrupted evidence. Tests use simulated storage; the real-driver configuration test disables networking.
- Atlas connector writes/readback were verified separately for two synthetic reports. The application still has no verified live MongoDB connection; current deployed storage remains disabled. See `MONGODB_READINESS.md`.
- A 390 × 844 Chrome viewport check observed readable wrapped results, no horizontal overflow, a blocked hardcoded repair and a passing correct formula with acceptance hidden. This is not an actual iPhone/Safari test. See `UI_QA_20261107.md`.
- No new deployment was created for this combined increment. The Vercel connector returned 404 for the saved project ID both with the AIZOYA slug and its returned team ID. Its filtered AIZOYA project listing returned no ReleaseProof project. This establishes a connector visibility blocker, not deletion of the previously observed preview. Browser state was not checked in this increment.

## Next concrete work

1. Restore or reconcile Vercel connector access to the existing `aizoya-releaseproof-demo` project before attempting another deployment. Preserve preview-only scope, authentication protection and the approved additional hosting ceiling of $5. Do not create a replacement project or change production domains to work around missing visibility.
2. Configure an approved least-privilege application credential and restricted network path for MongoDB, then verify actual application writes/readback and retries. Connector access alone cannot supply application authentication. Keep hosted acceptance disabled.
3. Configure agent identity securely, register on Agentverse and verify ASI:One discovery plus an actual chat round-trip.
4. Verify Meta balance/model/pricing and connect the implemented bounded repair handoff under Franklyn's $20 Meta fallback ceiling. Gemini and Subquadratic access remain unverified.
5. Complete actual iPhone/Safari and file-download checks. Record a one-minute actual product demonstration. Prepare submission for Franklyn's approval; confirm the event deadline from the current official rules before scheduling submission.

Full-repository and arbitrary Python repair remain outside this bounded prototype. Do not use it as an execution sandbox for customer code.
