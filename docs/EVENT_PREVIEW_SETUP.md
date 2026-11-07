# Event preview setup — November 7, 2026

## Authorized plan

Franklyn explicitly approved inspecting the signed-in dashboard and creating a
project in the AIZOYA team. Existing approval covers protected preview hosting
within the additional $5 demo ceiling. Production promotion remains excluded.

The signed-in dashboard confirms that the existing `aizoya-releaseproof-demo`
project and its saved project ID exist under the saved AIZOYA team ID. Its
production deployment dates to October 26. Standard Vercel Authentication is
enabled. No project setting was changed during inspection.

The Vercel connector identifies the same user and team, but cannot resolve the
existing project by name or ID. A direct creation request for a preview on that
exact project returned HTTP 403: no permission to create a Preview Deployment.
No new deployment was created. A separately authenticated CLI is not installed.
The reason for the connection's project-access denial is not established.

## Dry run

- Create `releaseproof-aie-20261107-preview` in the existing AIZOYA team only if
  absent. This is an isolated event preview environment using the same repository.
- Require Standard Vercel Authentication, keep source visibility private at the
  hosting layer, and do not attach Git automation or production domains.
- Preserve the existing production demo and all its domains/settings.
- Upload an explicit allowlist of tested source from this repository; exclude
  credentials, local database files, virtual environments and unrelated artifacts.
- Leave MongoDB and live AI providers disabled. No database or new paid service
  is created. Hosted acceptance remains disabled.
- Inspect returned project settings, then create only a preview deployment under
  the existing separate hosting approval. Verify status and the actual UI/API.
- Keep the approved additional $5 hosting ceiling. The previously observed
  team snapshot is not an enforceable project cost cap or isolated cost total.
- Record exact resulting IDs and live observations; do not describe creation,
  deployment or connectivity as successful until confirmed.

`aizoya.project.json` is the validated provisioning plan. Its disabled deployment
flags describe bootstrap scope; the separate recorded preview authorization
governs an explicit deployment action, and does not enable production.

## Verified creation result

- Created through the explicitly authorized signed-in browser using Vercel's
  empty-project option; the generated name `project-uun9v` was changed to
  `releaseproof-aie-20261107-preview` and the saved name/URL were read back.
- Project ID: `prj_sLpzFBw0BvbVUNZkE0H8mUXf5aWX`.
- Dashboard: https://vercel.com/aizoya/releaseproof-aie-20261107-preview .
- Standard Protection selected and Require Log In checked in the new project's
  deployment-protection settings. No bypass secret or shareable link was created.
- Overview reports both No Production Deployment and No Preview Deployments.
  No source was deployed, no Git automation was connected, and no database,
  model credential, custom domain or paid add-on was created.
- The connector rejected both preview creation on the legacy project and new
  project creation with HTTP 403. It also cannot resolve this browser-created
  project by its exact ID (HTTP 404). The browser and connector identify the same
  user/team; the underlying permission problem remains unresolved. Creation
  succeeds through the browser but does not fix connector deployment access.
- No build or serving workload was started here. Incremental invoiced cost was
  not measured; the existing team plan and spending controls were unchanged.

Next: establish a securely authorized deployment connection for this exact new
project, then deploy the reviewed source as a protected preview. Before publishing
the next branch update, reconcile remote history: the observed remote
`build/hosted-preview` reference was `390553b68937e7285d7214090a964b8e30cc6b32`,
while this checkout contains separate new local commits. Do not force-push or
deploy an unreviewed remote state.

## Source reconciliation and CLI preparation

Fetched and reviewed the published branch. Its runtime matched the earlier
preview; local MongoDB and response-timing changes were the substantive additions.
Merge `72355ee0e886167b4109038842dd130c6a6905a8` preserves both histories. The final
tree exactly matches local checkpoint `122b633`; no runtime code changed in this
merge. A normal push was attempted but rejected because this shell has no GitHub
write authentication. Do not describe this merge as published.

Official Vercel CLI 65.12.1 was installed as a task-local tool. There was no existing
CLI login or configured Vercel token; secure CLI device sign-in has been initiated
and awaits Franklyn's approval. No token or device authorization code is stored
in this repository. No deployment has started.

After sign-in: verify the authenticated user, link the exact existing new project
under scope `aizoya`, verify the project/team IDs against this record, and deploy
with explicit `--target preview`. Keep Standard Protection and provider storage
disabled. Use only the reviewed local source; never promote production or add a
custom domain as part of this fallback.

## Sign-in return and browser Git access blocker

Franklyn reported completing CLI device approval. On resuming, the CLI process
failed because workspace network policy blocks `https://api.vercel.com:443`.
No CLI login file or configured Vercel token was present afterward. Do not retry
the blocked network route or describe the CLI as authenticated.

The signed-in dashboard still opens the new project's Git settings. Existing
GitHub integration access can list repositories in namespace `aizoya`, but exact
search for `releaseproof-aie-20261107` returns No Results Found, with the explicit
instruction to grant Vercel access to the repositories to import. The Configure
GitHub App button opens GitHub's Vercel installation target-selection page. That
page did not finish returning its browser snapshot; its read-only inspection was
stopped. No repository grant, Git connection, deployment hook or build was created.

Next owner action: review Vercel's GitHub app installation for `aizoya` and grant
access only to `releaseproof-aie-20261107`. This is a new repository-access grant;
the owner must confirm it at action time. Afterward, verify repository visibility
and prepare a manual protected preview without enabling production automation.

## Vercel repository grant verified; source-write grant still missing

After Franklyn's next completion message, the Vercel GitHub selector successfully
found `releaseproof-aie-20261107` in namespace `aizoya`. The repository was connected
and the exact repository link was read back. This confirms Vercel's repository
grant is fixed and must not be requested again.

The ChatGPT GitHub connection could read the published branch head, still
`390553b68937e7285d7214090a964b8e30cc6b32`, but its create-tree call was refused
with HTTP 403, Resource not accessible by integration. No source tree, commit or
branch update was published. Vercel's GitHub app grant is distinct from the source
write access required by this connection.

Production tracking initially selected `main`. Attempts to save
`production-disabled` and turn off automatic domain assignment did not persist
after reload; do not claim those settings changed. The cause of the rejected or
unpersisted setting save was not established. The temporary Git connection was
then removed through the confirmation dialog, and the disconnected Git selector
was read back. This prevents leaving newly enabled production Git automation.
No deploy hook was created and no branch was pushed during this attempt.

Next owner action: review the GitHub installation/access for ChatGPT's connection,
include this exact repository and permit source updates through the normal
authorization flow. After source write access is verified, publish the tested
snapshot with a branch-head lease and establish a verified preview-only deployment
path before reconnecting automation. Do not ask for the Vercel repository grant
again or retry the network-blocked CLI route.
