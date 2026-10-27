# Decisions

> Each entry: the problem, the options we weighed, what we chose, and what we gave up. 🚪 marks decisions that are
> hard to reverse. To change one, add a new entry and mark the old one "Superseded by D-NN"; don't rewrite history.

| ID | Decision | Status |
|---|---|---|
| D-01 🚪 | ESPN is the only data source in v1 | Accepted, pending the spike |
| D-02 🚪 | Our own ids for players and users; ESPN ids as external keys | Accepted |
| D-03 | A bot ESPN account as co-manager supplies the cookies | Accepted |
| D-04 | Files in Cloud Storage, no database server; **no Firestore, ever** | Accepted |
| D-05 🚪 | Region `us-central1` | Accepted |
| D-06 | Go backend, TypeScript frontend, protobuf + Connect | Accepted |
| D-07 | **Separate deployables:** `web`, `api`, `sync` | Accepted (supersedes the single-service design) |
| D-08 | Sign-in through **Auth0**, tokens in headers | Accepted |
| D-09 | Access control in the app: a declared permission on every RPC | Accepted |
| D-10 🚪 | Metric registry; a change in meaning gets a new id | Accepted |
| D-11 | Terraform applied by the owner; CI deploys app code only | Accepted |
| D-12 | Formulas are similar to the sheet, not identical | Accepted |
| D-13 | Daily freshness; windows within the current season | Accepted |
| D-14 | Generated code is built, not committed | Accepted |
| D-15 | Start with a walking skeleton and a status page | Accepted |

## D-01 🚪 ESPN is the only data source

- **Problem.** League data exists only on ESPN. The sheet scraped basketball-reference by player name, which is
  fragile and against that site's terms. Paid stats APIs break the $0 goal.
- **Options.** ESPN only · ESPN plus basketball-reference with a name-matching layer · a paid API.
- **Decision.** ESPN only: per-game stats, rosters, settings, schedule, injuries, birthdates. Every date-range
  calculation is ours.
- **Gave up.** Advanced stats and pre-draft prospects, until a feature needs them. Accepted the unofficial-API
  risk, contained by one adapter package, kept raw responses, and a stale-data warning.

## D-02 🚪 Our own ids, ESPN ids as external keys

- **Problem.** Re-syncs must never renumber players; future sources (prospects, picks) won't have ESPN ids; a
  sign-in provider change must not orphan users.
- **Decision.** `player_id = espn:<athlete id>` (derived, so stable without a lookup table), with the ESPN id also in
  `external_ids`. User ids: the provider's id until we store per-user data, then our own id with provider links.
- **Gave up.** Opaque ids (UUIDs) for players, which would need a persistent mapping table we don't need yet.

## D-03 Bot ESPN account as co-manager

- **Options.** The owner's own cookie (exposes the whole ESPN account) · a public-view league (needs the league's
  consent, makes the league visible to anyone) · syncing only from the laptop · a bot account as co-manager.
- **Decision.** The bot account, with no commissioner rights, cookies in Secret Manager.
- **Gave up.** League-mates will see the co-manager. A leaked cookie could make moves on one team; the remedy is
  removing the co-manager.

## D-04 Files in Cloud Storage; no database server; no Firestore

- **Problem.** The data is a few MB per season and refreshed in bulk. Every managed database server costs money.
  The owner has ruled out Firestore.
- **Options.** Cloud SQL (≈$10/month) · Firestore (free, excluded) · files in a bucket plus in-memory compute.
- **Decision.** Normalized files in a bucket (one game-log file per day, one roster snapshot per day, reference
  files, a status file); the API holds the season in memory. Raw responses are archived for rebuilds only, never
  read while serving.
- **Gave up.** Ad-hoc SQL. When user-entered data arrives (league hub), a database is needed; options are listed in
  [data.md §6](data.md#6-when-we-need-a-database).

## D-05 🚪 Region `us-central1`

Free-tier eligible for Cloud Run and Cloud Storage. Changing regions later means moving everything.

## D-06 Go + TypeScript + protobuf/Connect

- **Options.** TypeScript end to end (shares formula code with the UI) · Go backend + TypeScript UI · Python.
- **Decision.** Go backend (`connect-go`), React + TypeScript frontend (`connect-es`), Buf for the contract. Formulas
  live only in Go; the UI renders.
- **Why.** The owner's preference and learning goal; fast cold starts; one typed contract generated for both sides.

## D-07 Separate deployables

- **Problem.** The first design served the UI from the API process, mainly so a session cookie would be
  first-party. The owner wants the UI and API to ship independently, which is also the more common practice.
- **Options.** One service serving both · two services under one custom domain with cookies · two services with
  token-based auth.
- **Decision.** Three deployables: `web` (static files), `api`, `sync`. The browser calls the API across origins with
  a bearer token; the API's CORS allows only the web origin.
- **Gave up.** The simplicity of one deploy. Tokens live in browser memory instead of an HttpOnly cookie, so the CSP
  and the provider SDK's token handling matter.

## D-08 Managed identity provider with bearer tokens

- **Problem.** Writing sign-in, sessions, and user management ourselves is the riskiest code in the system and
  doesn't fit separate deployables well. A users file shipped in the image was a stopgap the owner rejected.
- **Options.** Sign-in code in Go with Google · IAP in front of Cloud Run · a managed provider (Auth0, WorkOS
  AuthKit, Clerk). Tradeoffs in [security.md §8](security.md#8-choosing-the-identity-provider).
- **Decision.** A managed provider: **Auth0** (chosen for documentation and SDK maturity; WorkOS AuthKit was the
  runner-up). The API verifies tokens with Auth0's public keys and enforces permissions.
- **Gave up.** Independence from a vendor; the sign-in page on the vendor's domain.

## D-09 Access control in the app

- **Decision.** Coarse permissions (`authenticated`, `league.read`, `league.admin`, `app.admin`); every RPC declares
  one in its protobuf definition; an interceptor denies by default; a test requires the declaration. Roles come from
  token claims now and from our own database later.
- **Why.** Authorization stays ours regardless of provider, and "forgot to add auth" becomes impossible.

## D-10 🚪 Metric registry

- **Problem.** The owner wants to add player and team metrics easily.
- **Decision.** Every metric is a registered function with declared dependencies, computed column-wise; the API
  returns named columns plus a catalog; ids are stable and a meaning change gets a new id; weights are versioned
  parameters. An in-app formula editor is out of scope.

## D-11 Terraform applied by the owner; CI deploys app code only

- **Problem.** How do cloud resources get created and changed safely, and how does code get deployed, without
  giving an automated pipeline the keys to the whole project?
- **Options.**
  - *Click-ops in the console:* fastest, but not reproducible, and nobody remembers what was clicked.
  - *Terraform run by CI:* fully automated, but CI then needs project-admin rights, and a bad merge can delete
    infrastructure.
  - *Terraform run by the owner, CI deploys only app code:* reproducible, reviewable, and the CI identity can only
    push images and update Cloud Run.
  - *Deploy from source with `gcloud run deploy --source`:* simple, but it leaves build artifacts behind and mixes
    building with deploying.
- **Decision.** The third option. Two details that avoid classic mistakes: Terraform creates secrets but never their
  values (so no secret lands in state), and Cloud Run resources ignore the image field (so `apply` never undoes a
  deploy). PR jobs get no cloud credentials; the deploy identity is restricted to this repo's `main`.
- **Gave up.** Fully hands-off infrastructure changes; the owner runs `terraform apply`.

## D-12 Similar to the sheet, not identical

The sheet is a behavior reference. [formulas.md](formulas.md) defines the app's own formulas and their worked
examples. Intended differences so far: weeks follow ESPN's matchup periods; projections use position-aware lineups
and skip OUT players; the sheet's team-strength formula and the R.E roster slot are dropped; roster sizes come from
ESPN settings.

## D-13 Daily freshness; windows within the current season

No start/sit job means daily data is enough; the sync re-fetches the last 7 days; windows never cross seasons.

## D-14 Generated code is built, not committed

- **Problem.** Protobuf generates Go and TypeScript code. Committing it is convenient but noisy and can drift.
- **Decision.** Generated directories are git-ignored; `make gen` produces them locally, and CI generates before
  building and testing. A freshness check isn't needed because nothing generated is in the repo.
- **Gave up.** `go build` straight after a fresh clone; `make setup` and `make gen` come first.

## D-15 Walking skeleton first

- **Decision.** Milestone 1 deploys an empty `web` and `api` with a status page through the full CI/CD path before
  any ESPN or league feature. Sign-in is M2, sync is M3.
- **Why.** It proves the riskiest plumbing (build, deploy, permissions, cost) while the code is trivial, and every
  later milestone is a small increment on a working system.

## Accepted tradeoffs (known deviations from textbook practice)

| # | Deviation | Why | Mitigation | Revisit when |
|---|---|---|---|---|
| T-1 | No staging environment | $0 | Fixture-based `make dev`, PR CI, smoke-tested no-traffic revisions before traffic moves | League-mates depend on uptime |
| T-2 | Branch protection is honor-system (GitHub Free, private repo) | $0 | Pre-push hook, the deploy workflow's merged-PR guard, agent deny-lists | Going public, or a second committer |
| T-3 | Dependence on an identity-provider vendor | Removes all sign-in code and the users file | Standard OIDC; our own user ids once we store user data | The vendor's free tier changes |
