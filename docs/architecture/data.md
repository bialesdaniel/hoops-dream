# Data

> What data the app keeps, how things are identified, where the data lives, and why. Implementation specifics
> (proto field layouts, Go types) belong in the code and in [`proto/AGENTS.md`](../../proto/AGENTS.md).

## 1. Core concepts

These are the nouns the whole app is built from. Each one answers a question.

| Concept | Answers | Notes |
|---|---|---|
| **League season** | "Which league, which year?" | A league persists across years; ESPN gives each year a `seasonId` (named by the year the season **ends**: 2026-27 is `2027`). Everything league-specific is keyed by **both** `league_id` and `season`, so one league naturally has many seasons, and a test league is just another `league_id`. |
| **League settings** | "What are the rules?" | Scoring weights, lineup slots, matchup periods (fantasy weeks, including the two-week ones), playoff weeks, the trade deadline. Always read from ESPN, never hard-coded. |
| **Team** | "Who are the 16 managers' teams?" | Name, division, and the current roster: which players, and whether each is in an IR slot. |
| **Player** | "Who is this person?" | Name, position(s), eligible lineup slots, current NBA team, birthdate, injury status. |
| **Game log** | "What did a player do in one game?" | One row per player per NBA game: minutes, shooting, rebounds, assists, steals, blocks, turnovers, points, plus ESPN's own fantasy-point total for cross-checking. Every window stat (season, last 30 days, one night) is computed from these. |
| **Schedule** | "Who plays when?" | For each NBA team, its games by day. Drives projections and the schedule planner. |
| **Day** (scoring period) | "Which game day?" | ESPN numbers each day of the NBA season (opening night = 1) and uses those numbers everywhere in its API. We keep ESPN's number **and** the calendar date, because the schedule and humans think in dates. ⏳ The spike confirms ESPN's day boundary is US/Eastern. |
| **Matchup period** | "Which fantasy week?" | An ordered list of days. Comes from ESPN settings. Some periods cover two calendar weeks. Weeks are never derived from calendar Sundays. |
| **Roster snapshot** | "What did each team look like on a given day?" | Saved by every daily sync. The source for history and team trends later. |
| **Matchup score** (M7) | "What has each team actually scored this week?" | ESPN's official totals per day; used for "actual so far" in projections. |

## 2. How things are identified

Why this matters: data from different ESPN endpoints, and later from other sources, must line up reliably, and
re-running the sync must never renumber anything.

- **Players:** our own `player_id`, written as `espn:<ESPN athlete id>` for players that come from ESPN. It is
  derived, so it's stable across re-syncs with no lookup table. The ESPN id is also kept in `external_ids` under
  the key `espn`. When another source arrives (e.g., draft prospects who don't exist in ESPN), they get another
  prefix and their ids go in `external_ids` too. In practice the ESPN id is the only one used until then, which is
  exactly the intent.
- **Teams:** `(league_id, season, team_id)` using ESPN's per-league team id.
- **Users:** Auth0's user id for now. When we store per-user data (league hub), we create our own `user_id` and link
  provider identities to it, so changing providers never orphans anyone.
- **Days:** ESPN scoring period id, plus the date.

## 3. Where the data lives

### Why files, not a database

The data is small (about 30k game-log rows per season, a few MB) and refreshed in bulk once a day. That profile
fits **files in a Cloud Storage bucket** better than a database: free, nothing to operate, and easy to rebuild. The
API loads the current season into memory and computes on the fly.

### The three kinds of files

| Kind | What's in it | Who reads it | Why it exists |
|---|---|---|---|
| **Normalized data** | Our own, compact, typed files: one **game-log file per day** holding every player's box score for that day; a **roster snapshot per day**; and a few **reference files** (players, NBA schedule, league settings). | The API, on every request (from memory). `make replay` and tests. | This is the data the app runs on. Shaped for our needs, not ESPN's. |
| **Status file** | One small JSON per league season: when the last sync succeeded, when it last ran, the last error, the latest day with data. | The API (for "Data as of" and the stale warning), the status page, monitoring. | One place that says whether the data can be trusted. |
| **Raw archive** (optional) | The exact ESPN responses, gzipped, with login material scrubbed. | **Nothing at serve time.** Only `make replay` (rebuilding normalized files after a parser fix or when a new field is needed) and debugging. | Lets us add a stat or fix a parsing bug for past days without asking ESPN again, and shows exactly what ESPN sent when something looks wrong. Costs cents. Can be dropped if we decide re-fetching from ESPN is enough. |

Nothing is ever computed from raw responses while serving. The sync shapes ESPN's responses into normalized files
once; the API reads only normalized files.

### Layout

The local `./data` folder uses the same structure.

```text
nba/{season}/players.pb.gz                          # reference: bios, positions, eligible slots, birthdates, injuries
nba/{season}/schedule.pb.gz                         # reference: NBA schedule
nba/{season}/gamelogs/{date}.pb.gz                  # all players' box scores for one day
leagues/{league_id}/{season}/settings.pb.gz         # league settings + teams (current rosters)
leagues/{league_id}/{season}/rosters/{date}.pb.gz   # roster snapshot for one day
leagues/{league_id}/{season}/matchups.pb.gz         # M7: official weekly scores
leagues/{league_id}/{season}/status.json            # last sync result
raw/{season}/{date}/{label}.json.gz                 # archive; deleted after 400 days
```

The normalized files are protobuf messages (defined under `proto/`, storage package), gzipped. Protobuf gives us a
schema with evolution rules for free; nobody edits these files by hand.

**Status file fields:** `schema_version`, `last_success`, `last_attempt`, `last_error`
(`null | espn_auth | espn_unavailable | parse_error`), `latest_day`. "Stale" means more than 36 hours since
`last_success`, or a non-null `last_error`.

### How a sync updates the files

1. Fetch from ESPN (details in [espn.md](espn.md)); optionally archive the raw responses.
2. Write the reference files (players, schedule, settings) first, so that any player appearing in today's game logs
   already exists.
3. Write one game-log file per fetched day. The last 7 days are rewritten every run, which absorbs ESPN's stat
   corrections; a day's file is always complete for that day.
4. Write today's roster snapshot.
5. Write the status file last.

Every file write is atomic (Cloud Storage replaces an object whole or not at all), and rewriting a day's file with
the same data is harmless, so re-running a sync is always safe. The API re-lists the bucket about once an hour and
reloads only files whose version changed.

## 4. Robustness review

The owner asked whether this is fragile. The risks and what covers each:

| Risk | What happens | Mitigation |
|---|---|---|
| ESPN changes a response shape | Parsing fails for one endpoint | The sync stops before touching normalized files for that data, records `parse_error` in the status file, and keeps serving yesterday's data (marked stale). Fix the parser in the one package that knows ESPN, record new fixtures, replay from the raw archive. |
| A sync dies halfway | Some files updated, others not | Each file is complete and consistent on its own; reference files are written before day files; the status file isn't updated, so the stale warning fires after 36 h. The next run repairs everything, because every write is idempotent. |
| Two syncs overlap (scheduled plus manual) | Both write the same files | A lock object created with a "must not exist" precondition makes the second run exit early; the lock expires after 2 h in case a run crashed. |
| A bug or a person overwrites or deletes a file | Data loss | Bucket object versioning is on; a previous version can be restored. Normalized files can be rebuilt from the raw archive; raw and game logs can be re-fetched from ESPN. The only irreplaceable files are roster snapshots, and they're also versioned. |
| The API reads while the sync writes | A request sees day N updated and day N−1 not yet | Each day file is self-consistent; the worst case is a stat correction appearing an hour later. |
| A player appears in game logs but not in the players file | Unknown player | Reference files are written first; the API also tolerates it by showing the id until the next refresh. |
| We add a new stat or metric that needs past days | Backfill | Replay from the raw archive, or re-fetch from ESPN, which serves the whole current season. |
| The data outgrows memory | Slow API | It won't for a 16-team league (a few MB per season); if it ever did, load only the current season and read older seasons on demand. |
| Schema changes in normalized files | Old files unreadable | Protobuf field rules plus a `schema_version` in the status file; a migration is a replay. |

The simplest thing that could fail silently is a sync that stops running (e.g., Scheduler misconfigured). The stale
warning in the app and the daily GitHub health check cover that ([devops.md §4](devops.md#4-knowing-it-works-monitoring-at-0)).

## 5. Recorded fixtures

Agents and CI can't reach ESPN, so recorded responses are their only ESPN. A fixture set is a folder
`backend/internal/espn/testdata/<date>/` containing the spike's (or `make sync`'s) raw output as-is: `<label>.json.gz`
files plus `meta.json` (league id, season, capture time, latest day). `make replay` turns the newest fixture set into
a local `./data`. Fixtures are already scrubbed of ESPN member ids when written; team and manager names remain,
which is why the repo is private.

## 6. When we need a database

Nothing in M1–M10 stores user-entered data, so there is no database. The league hub (pick tracking, trades, the
draft) will need one. **Firestore is excluded by the owner's decision.** When the time comes, the candidates are:

| Option | Cost | Notes |
|---|---|---|
| Cloud SQL (Postgres) | ≈ $10/month | The boring choice on GCP; the only ongoing cost in the system |
| An external serverless Postgres with a free tier (e.g., Neon) | $0 | Another vendor; fine for tiny data |
| SQLite on Cloud Storage | $0 | Clever but unusual; single writer only |

Deferred until a feature needs it.
