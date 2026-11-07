# MongoDB readiness — November 7, 2026

## Verified

The authorized MongoDB Atlas connection can inspect the existing AIZOYA
organization and read/write synthetic development evidence.

- Organization: `6acafcc71b25c552793541ed`.
- Existing project: `Project 0`, ID `6acafcc71b25c552793541fd`.
- Existing cluster: `Cluster0`, FREE tier, AWS `US_WEST_2`, IDLE, not paused.
- Isolated database: `releaseproof_aie_20261107_dev`.
- Collection: `verification_evidence`.
- Two new reports were generated locally from the event-built verifier and stored
  through the Atlas connector. Full document readback exactly matched both originals.

| Document ID | Fixture | Checks passed | Result |
| --- | --- | --- | --- |
| `atlas-smoke-v1-hardcoded-20261107` | Synthetic hardcoded total | 1/40 | fail / blocked |
| `atlas-smoke-v1-correct-20261107` | Synthetic correct formula | 40/40 | pass / eligible |

Both reports use schema 2, engine `bounded-ast-v2`, and replay seed `20261107`
stored as text. Documents contain synthetic source and actual verifier results,
not customer data, provider credentials, or model-generated output. Fixed document
IDs were checked for absence before insertion. No acceptance action was performed.

No new cluster, paid tier, database user, IP allowlist, or billing setting was
created or changed. This check does not reverify promotional credit balance.

## Still blocked

The Vercel preview is **not connected to MongoDB**. Connector access is not an
application credential. The preview remains stateless, with acceptance disabled.
No claim of deployed durable storage, immutable evidence, or production readiness
follows from this connector persistence check.

Next: configure a securely stored, least-privilege application credential scoped
to the development database; establish an approved restricted network path;
verify the prepared application adapter against the live database.
Do not place connection credentials in chat, source, or public documentation.

## Prepared application adapter (not deployed)

`releaseproof/mongo_store.py` adds optional PyMongo storage and is wired into
`/api/verify` only when `RELEASEPROOF_STORAGE=mongodb` is explicitly enabled.
Install `requirements-mongodb.txt` in a future approved storage-enabled build.
Use the existing development database and a separate `application_evidence_v1`
collection; the earlier connector smoke-test records remain separate.

- A shared lazy client is reused across warm serverless requests; no connection
  is created by importing the module. TLS and majority write acknowledgment apply.
- Initial pool cap is 3 with no prewarmed connections, assuming a low-concurrency
  demo on the free cluster. Per-operation timeout is 2.5 seconds, with selection
  and connection deadlines of 2 seconds, below the 10-second function limit.
  These provisional settings require real network latency and concurrency checks.
- Every successful submit must write, read back and replay evidence. Storage or
  replay errors return blocked responses without exposing driver messages.
- Optional SHA-256 `Idempotency-Key` requests converge on one unique MongoDB `_id`;
  changed content is rejected. Without a key, separate requests create separate runs.
- The preview does not expose public run lookup or enable hosted acceptance.
- Storage remains disabled in the current deployed preview. Local behavioral
  tests use simulated collections. A separate real-driver configuration check
  disables networking; neither establishes live application connectivity.

After secure runtime setup, verify actual application writes and retries, then
monitor Atlas connection count, pool checkout failures and verification latency.
Avoid recording candidate source, credentials or driver exception payloads in
monitoring. Do not increase pool size or cluster tier without measured need.
