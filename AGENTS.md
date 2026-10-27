# AGENTS.md: hoops-dream

hoops-dream is a fantasy basketball companion app for one 16-team ESPN league
(head-to-head points, dynasty-style). It replaces a manual Google Sheet with
synced rosters, player values, a roster sandbox for testing moves, projections,
and playoff planning. Personal use first; later the league's shared hub.

**How work happens:** the owner sends instructions milestone by milestone. Don't
pick up work from the roadmap on your own; do read the docs for the area you're
asked to touch.

**Status:** design docs only; no code yet. First milestone: M1 walking skeleton
([roadmap](docs/product/roadmap.md)).

## Read before you work

| When you…                                    | Read                                                                                                                                                             |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Start any task                               | The feature doc for what you're building ([docs/product/features/](docs/product/features/README.md)) and the active plan in `docs/plans/active/` if there is one |
| Need product context                         | [docs/product/overview.md](docs/product/overview.md)                                                                                                             |
| Touch any number or metric                   | [docs/architecture/formulas.md](docs/architecture/formulas.md), the source of truth. "FPTS" means fantasy points.                                                |
| Need the big picture                         | [docs/architecture/overview.md](docs/architecture/overview.md)                                                                                                   |
| Work in `backend/`, `frontend/`, or `proto/` | That folder's `AGENTS.md` (coding conventions), plus [backend.md](docs/architecture/backend.md) / [frontend.md](docs/architecture/frontend.md)                   |
| Touch data, storage, or ids                  | [docs/architecture/data.md](docs/architecture/data.md)                                                                                                           |
| Touch ESPN code or fixtures                  | [docs/architecture/espn.md](docs/architecture/espn.md)                                                                                                           |
| Touch auth, CORS, headers, secrets           | [docs/architecture/security.md](docs/architecture/security.md)                                                                                                   |
| Touch infra, CI/CD, deploys                  | [docs/architecture/devops.md](docs/architecture/devops.md)                                                                                                       |
| Write or change tests                        | [docs/architecture/testing.md](docs/architecture/testing.md)                                                                                                     |
| Want to change a decision                    | [docs/architecture/decisions.md](docs/architecture/decisions.md): propose first                                                                                  |

## Commands

The Makefile is self-documenting: **run `make help`** for the current list with
descriptions. This file doesn't duplicate it. Two rules: `make check` must pass
before you ask for verification, and run `make gen` after any `.proto` change
(generated code is not committed).

## How to work

1. **Confirm the ask.** Restate what you'll build and which feature doc it maps
   to. For multi-step work, write a plan in `docs/plans/active/` (template in
   [docs/plans/README.md](docs/plans/README.md)); save plans **there**.
2. **Build in the smallest self-contained changes.** A feature usually lands as
   a short sequence of independent changes, each passing `make check` and each
   verified on its own: first the API contract (new proto fields or RPCs,
   backward compatible and not yet used), then the backend implementation with
   tests, then the frontend that consumes it. Never bundle all three into one
   large change, and never build the whole backend before any UI exists.
3. **Formulas:** write the worked-example tests from formulas.md first, then the
   code.
4. **ESPN:** never call ESPN from tests or CI; use the recorded fixtures and
   `make replay`.
5. **Keep the docs true.** When behavior changes, update the relevant
   engineering doc **and the feature doc** (its stories, acceptance criteria,
   history) in the same PR. If a goal or non-goal changes, update
   `docs/product/overview.md` too.
6. **Unknowns:** record them as open questions in the plan or feature doc
   instead of guessing.
7. **Manual verification before committing.** When the work is done and
   `make check` passes, **stop**. Give the owner verification steps (what to
   run, what to open, what to expect). Commit and open the PR only after the
   owner confirms. Put the same steps in the PR under "How to verify".

## Boundaries

**Always**

- Keep every ESPN response shape inside `backend/internal/espn`, and scrub
  member ids from any fixture you record.
- Return `data_as_of` and `stale` in API responses. Show missing values as
  missing, never silently 0.
- Declare a permission on every RPC.

**Ask the owner first**

- A dependency that isn't in the pre-approved list in the folder's `AGENTS.md`,
  or any new cloud service.
- Changing a shipped `.proto` contract, a metric id or meaning, formula weights,
  or worked examples.
- Changing `docs/architecture/decisions.md`, Terraform, the deploy workflow, or
  IAM outside an approved plan.

**Never**

- Run `gcloud`, `terraform apply`, or `make rotate-espn-cookies`, or touch the
  live GCP project. Owner-only.
- Read, print, or commit ESPN cookies or any secret. Cookies live outside the
  repo.
- Weaken, skip, or delete a failing test, or edit its expected values, to make
  it pass.
- Push to `main`, or use `git push --no-verify`. Work on a branch and open a PR.
- Hand-edit generated code, or commit it.
- Loosen the CSP or other security headers, log tokens or emails, or pin a
  GitHub Action by tag instead of SHA.
- Add paid or fixed-cost cloud resources: load balancers or forwarding rules,
  `min-instances` > 0, always-on CPU, Cloud NAT, static IPs, Cloud SQL,
  Memorystore, anything outside `us-central1`.
- Derive fantasy weeks from calendar Sundays; use ESPN matchup periods.

## Definition of done

- `make check` passes, and new behavior has tests (formula changes include
  worked examples).
- The owner has manually verified the change (step 7 above).
- Engineering docs and the feature doc are updated; the plan's Progress and
  Outcome are filled in.
- UI changes include a screenshot in the PR.
- No new lint warnings; no TODOs without a linked open question.

## Gotchas

- "FPTS" = fantasy points; "PTS" = NBA points.
- Some fantasy weeks span two calendar weeks.
- ESPN names a season by the year it ends: 2026-27 → `2027`.
- Player ids are deterministic (`espn:<athleteId>`).
- Cloud Run gives CPU only while a request is in flight: no background timers.
- The web app and the API are different origins; the API's CORS allows only the
  web origin.
- Tool deny-lists are committed (`.claude/settings.json`,
  `.gemini/settings.json`); keep them in sync with "Never".
