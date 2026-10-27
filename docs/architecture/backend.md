# Backend

> The `api` service and the `sync` job: one Go module, two binaries. This doc
> explains how each works and why. Coding conventions live with the code in
> [`backend/AGENTS.md`](../../backend/AGENTS.md).

## What the backend does

1. **Sync** (daily job): fetch data from ESPN, store it, derive our own
   normalized data, and publish it atomically.
2. **Serve** (API service): load the published data into memory, verify callers,
   compute metrics and projections on request, and return typed responses.

## Packages, in plain words

| Package                | What it does                                                                                                                                                                                  | Why it's separate                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `cmd/api`, `cmd/sync`  | The two programs. They read configuration from environment variables and wire the packages below together.                                                                                    | Entry points stay tiny; logic lives in packages that tests can exercise.                              |
| `internal/espn`        | Talks to ESPN: builds requests, parses responses into our own types, knows ESPN's ids and quirks.                                                                                             | **The only package allowed to know ESPN's shapes.** When ESPN changes, this is the only place to fix. |
| `internal/ingest`      | The sync pipeline: fetch → normalize → write per-day files and reference files → write the status file. Also the offline `--replay` mode that runs the same pipeline from recorded responses. | The pipeline is testable without ESPN by replaying fixtures.                                          |
| `internal/storage`     | A small interface for "put/get a file", with two implementations: the Cloud Storage bucket (prod) and a local folder (laptop and tests).                                                      | The same sync and API code runs locally and in the cloud; tests use temp folders.                     |
| `internal/domain`      | Our own types: league settings, team, player, game log, schedule, matchup period, roster snapshot. No ESPN field names.                                                                       | Everything downstream speaks our language, not ESPN's.                                                |
| `internal/metrics`     | The metric registry and the metric functions (FPTS, FPPG, ranks, EDSA, …), plus versioned parameters such as EDSA weights.                                                                    | New metric = one function here. See below.                                                            |
| `internal/projections` | Daily lineup fitting and period projections (formulas §9–10).                                                                                                                                 | Different shape from registry metrics (needs schedule and injuries); kept apart for clarity.          |
| `internal/api`         | The Connect RPC handlers and interceptors: token verification, permission checks, request logging.                                                                                            | Handlers only translate between RPC messages and domain calls.                                        |
| `internal/auth`        | Token verification against the identity provider, and the permission check used by the interceptor.                                                                                           | Small and isolated, since it's security-sensitive.                                                    |
| `gen/`                 | Code generated from `proto/` at build time. Not committed.                                                                                                                                    | `make gen` regenerates it; CI regenerates before building.                                            |

## The sync pipeline

The sync produces three kinds of files (full explanation in
[data.md §3](data.md#3-where-the-data-lives)):

| Kind                       | What it is                                                                                                                                                                    | Read by                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Normalized data**        | Our own typed files: one game-log file per day (every player's box score that day), one roster snapshot per day, and reference files (players, NBA schedule, league settings) | The API, from memory, on every request                  |
| **Status file**            | A small JSON: last successful sync, last attempt, last error, latest day with data. It is what "Data as of" and the stale warning are based on.                               | The API, the status page, monitoring                    |
| **Raw archive** (optional) | The exact ESPN responses, scrubbed of login material                                                                                                                          | Nothing at serve time; only `make replay` and debugging |

The point of normalizing first is that **the API never touches ESPN's shapes**:
the sync reshapes responses once, into files designed for our questions.

Steps in order:

1. Load the bot account's cookies (Secret Manager in prod; a file outside the
   repo on the laptop).
2. Fetch, at most one request per second: league settings, teams and rosters,
   the player pool with injuries, per-game stats for everyone in the pool (last
   7 days normally; the whole season on the first run), the NBA schedule, and
   birthdates for players we haven't seen. (Matchup scores are added in M7.)
3. Archive raw responses, scrubbing ESPN member ids (they double as login
   cookies).
4. Write the reference files, then one game-log file per fetched day, then
   today's roster snapshot.
5. Write the status file last.

Each file write is atomic and rewriting a day with the same data is harmless, so
re-running the job is always safe. Re-fetching the last 7 days absorbs ESPN's
stat corrections. A lock file stops two syncs from overlapping.

**Replay:** `cmd/sync --replay <fixture folder>` runs steps 3–5 from recorded
responses. This is how `make dev` gets realistic data with no credentials, and
how CI tests the pipeline.

## The API service

- **Startup:** read the status file, load the season's normalized files into
  memory (a few MB).
- **Freshness:** on each request, if the bucket hasn't been checked in the last
  hour, list it and reload only the files whose version changed. There are no
  background timers, because Cloud Run only gives CPU to a request that is in
  flight.
- **Per request:** verify the bearer token → check the RPC's declared permission
  → compute → respond. Every response includes `data_as_of` and `stale`.
- **Health:** `GET /healthz` (process is up) and `GET /statusz` (data freshness
  as JSON, nothing sensitive, HTTP 503 when stale). Both are unauthenticated and
  used by the status page and by monitoring.
- **CORS:** only the web app's origin may call the API from a browser.

## The metric registry

Goal: adding a metric is **one Go function + one registration + one
worked-example test**, with no change to the API contract or the UI.

- A registration declares: `id` (stable, snake_case), label, description, scope
  (`player` or `team`), display format, whether higher is better, whether it
  shows on phones, and which other metrics it depends on.
- Metrics are computed **as whole columns** (all players at once), in dependency
  order. This matters because ranks and scaling need the whole population.
- Inputs available to a metric: game logs, rosters, schedule, injuries, league
  settings, the selected window, the as-of date, and versioned parameters (e.g.,
  EDSA weights).
- The API returns metric values as named columns (`metric_ids` once, then one
  row of values per player) and offers a `ListMetrics` catalog; the UI builds
  columns from the catalog.
- Rules: a metric's meaning never changes under the same id (make `edsa_v2`
  instead); every metric has a worked example in [formulas.md](formulas.md); a
  test fails if an id disappears or a dependency cycle appears.
- Projections are typed RPCs, not registry metrics: they return per-period
  numbers and lineups rather than a single column.

## Configuration (environment variables)

| Variable                        | Used by           | Example                                                    |
| ------------------------------- | ----------------- | ---------------------------------------------------------- |
| `ESPN_LEAGUE_ID`, `ESPN_SEASON` | sync, api         | `123456`, `2027` (ESPN names a season by the year it ends) |
| `ESPN_COOKIES_FILE`             | sync (laptop)     | `~/.config/hoops-dream/espn.env`, outside the repo         |
| `DATA_DIR`                      | sync, api (local) | `./data`                                                   |
| `GCS_BUCKET`                    | sync, api (prod)  | `<project>-hoops-dream-data`                               |
| `PORT`, `LISTEN_ADDR`           | api               | `8080`, `127.0.0.1` locally                                |
| `AUTH_ISSUER`, `AUTH_AUDIENCE`  | api               | the identity provider's issuer URL and our API identifier  |
| `CORS_ORIGINS`                  | api               | the web app's URL(s)                                       |

Non-secret defaults are in `.env.example`; copy it to `.env.local`
(git-ignored).

## Local development

- `make dev` runs the API on `127.0.0.1` with data from `./data` (running
  `make replay` first if it's empty) and the web app's dev server. Sign-in uses
  the real identity provider with `http://localhost:5173` allowed as a callback,
  so there is no fake login path in normal use.
- For automated tests and agents without a browser, API **dev builds**
  (`-tags devauth`) accept a locally minted token. That code is not compiled
  into production images and refuses to run on Cloud Run.
- `make sync` runs a real sync into `./data` using your cookies file.
