# Protected verification preview — November 7, 2026

## Live result

- URL: https://aizoya-releaseproof-demo-hbk9doal4-aizoya.vercel.app/
- Vercel deployment: `dpl_3aH77KqYJvdSaK7smh5iV4aFdy5u`, state READY, preview target (target null), no aliases assigned.
- Project: existing `aizoya-releaseproof-demo` / `prj_GOnohMW76ekvtPyJ0Ar06JzBH5tg`.
- Runtime source: local Git commit `eb8dbb23f75a67456ce90a0e82395eeb2bc9abff`; public branch is synchronized by content after deployment.
- 56 local tests passed, including exact 64-bit seed replay and HTTP evidence export. Browser JSON keeps schema-v2 replay seeds as text.

## Observed live browser checks

- Preview loaded with explicit verification-only / no persistent evidence notice.
- Original delivery-omission defect reproduced (38 of 40 checks failed on the earlier equivalent evaluation build).
- Final build hardcoded $130 candidate: visible example passed; 39 of 40 checks failed; BLOCKED.
- Final build correct formula: 40 of 40 checks passed; ELIGIBLE; acceptance remained disabled.
- Final build unsupported `import os`: INCONCLUSIVE / BLOCKED, zero checks executed.
- Changing candidate text cleared the previous displayed verdict.
- Rendered evidence: schema 2, string replay seed, 40 actual check results, `storage: not-persisted`.
- Unauthenticated external API requests encountered Vercel authentication; direct acceptance request received HTTP 401. Protection was not bypassed or weakened.

The HTTP report-export implementation is covered locally and uses an attachment response with replay of the exact original seed. Cloud Browser's file retrieval failed for both Blob and HTTP downloads; downloading the final file is **not verified in that browser**. The JSON remains readable in the evidence panel. Do not claim successful end-user file saving or an iPhone browser test.

## Costs and boundaries

Franklyn approved up to $5 additional hosting, separate from the $20 Meta fallback. Refreshed Vercel team snapshot after builds: $18.48 used / $20 included infrastructure credit, current on-demand spend $0. This is a team-wide snapshot, not a final invoice or isolated project-cost attribution; usage can lag. The earlier snapshot was $18.45 / $20. Team budget settings were not changed.

One initial build failed because the existing project required a file-based `/api` entrypoint. Subsequent previews corrected the entrypoint and improved evidence export. No production alias/domain was promoted, no model API was called, and no competition submission occurred.

## Remaining operational blockers

- Durable MongoDB evidence store and secure URI not connected. Hosted acceptance intentionally returns 503/blocked in local endpoint tests and is absent from the live interface.
- No live Meta, Gemini or Subquadratic calls. Imported provider output remains unverified provenance.
- uAgents adapter tested offline only; no hosted ACP endpoint, Agentverse registration or ASI:One discovery/round-trip for this agent.
- iPhone/mobile visual QA and actual file-download confirmation remain pending.
- This is a bounded synthetic arithmetic verifier, not a general repository repair sandbox or production release.
