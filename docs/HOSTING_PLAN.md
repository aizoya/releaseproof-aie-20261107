# Hosted preview plan — November 7, 2026

## Prepared implementation

Branch: `build/hosted-preview`, based on public source commit `9cfab9a81ef70b1ed2f80de974454b503450c548`.

- WSGI application entrypoint `app.py` / `releaseproof.preview.app`, following Vercel's documented Python entrypoint support.
- Standard-library runtime only; ten-second configured function duration.
- Existing web interface and synthetic fixtures included explicitly.
- Verification is real bounded evaluation. No general Python execution, repository fetching or external model calls.
- No local database writes in hosted mode. Reports say `storage: not-persisted` and offer evidence download.
- `POST /api/accept` returns 503/blocked, including after a passing verification. Missing persistence cannot approve a candidate.
- Local CLI/server still support persisted SQLite evidence and explicit local acceptance.
- Preview labels and controls reflect server capabilities. Edited candidate source clears the old verdict.
- 52 tests passed locally with optional ACP dependencies; no Vercel build or hosted browser QA has occurred.

## Proposed deployment

Use the existing AIZOYA Vercel project `aizoya-releaseproof-demo`, ID `prj_GOnohMW76ekvtPyJ0Ar06JzBH5tg`, as a **preview deployment only**, with existing authentication protection. Do not replace its production deployment or move `releaseproof.aizoya.com`. Do not connect automatic production deploys while preparing this preview. Reuse the new event source; do not present the older project's code as event work.

The preview proves only the bounded verifier UI/API. It is not an ACP endpoint and cannot complete an ASI:One agent integration. It must not be presented as a deployed end-to-end ReleaseProof service.

## Verified hosting-account facts

Read-only Cloud Browser check of the AIZOYA Vercel billing page:

- Pro plan active, billing cycle October 13–November 13, 2026.
- Included infrastructure credit: $18.45 used / $20.00; approximately $1.55 unused at the observed snapshot.
- Current on-demand spend displayed: $0.
- Existing team on-demand budget: $200; automatic pause OFF. This is not a project-specific $0 cap.
- Existing recurring invoice displayed: $20; this was not created or changed by this work.

Included credit and spend change as other projects run. The observed remaining credit does not guarantee that another deployment creates no incremental charge. No deployment, billing change or team-budget change occurred. Franklyn's existing $20 fallback applies to Meta only, not hosting.

## Approval / connection gates

1. Confirm a hosting overage allowance, or establish a suitable no-overage boundary, before paid-capable deployment. Do not alter company-wide spending controls without explicit permission.
2. Secure provider configuration is absent: no Meta key, Gemini key, MongoDB URI or agent seed/endpoint is configured in this workspace. The existing Vercel project's listed environment-variable set is empty; this does not establish team-wide credential availability.
3. Connect MongoDB using the existing credited account through a secure provider/runtime flow. Verify actual durable evidence storage before enabling hosted acceptance.
4. Establish an ACP-capable runtime, register the agent and observe an actual ASI:One request/response and discoverability.
5. Verify live model access and costs independently; no imported response is proof of live Meta usage.

No credentials belong in chat, source, evidence downloads or Git history. No provider connection is claimed from account existence alone. No competition submission is authorized by this hosting plan.

Official references:
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/runtimes/python/api-directory
- https://vercel.com/docs/spend-management
