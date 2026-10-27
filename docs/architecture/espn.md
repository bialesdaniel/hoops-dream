# ESPN Integration

> How we get data out of ESPN, what can go wrong, and what the spike still has
> to confirm. Endpoint and field reference lives in the owner's OpenAPI docs
> (<https://bialesdaniel.github.io/espn-fantasy-api>); this doc doesn't
> duplicate them. The `cwendt94/espn-api` Python library
> (<https://github.com/cwendt94/espn-api>) is the other reference for
> undocumented views.

## 1. The situation

ESPN's fantasy API is **unofficial and undocumented**. Its terms restrict
automated access, and it can change without notice. The owner accepted this risk
for low-volume, read-only use. Consequences for the design:

- **One package** (`backend/internal/espn`) knows ESPN's shapes. Nothing else
  does.
- **Raw responses are archived**, so a parser fix or a new field can be applied
  to past days without ESPN. Nothing reads the archive while serving.
- **Recorded responses are the test fixtures**, because CI and agent sandboxes
  can't reach ESPN.
- If ESPN breaks, the app shows **stale data with a warning** until the adapter
  is fixed.

## 2. Which ESPN APIs, and why these

ESPN runs several API families with different version numbers; the numbers
aren't comparable across families.

| Family                      | Base                                                                                                                  | Version | We use it for                                                                                                                                                                                    |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Fantasy "league reads"      | `https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{season}`                                            | v3      | League settings, teams, rosters, player pool with injuries, **per-game stats** (batched 50 players per call, with ESPN's own fantasy-point totals), NBA schedule, transactions and draft (later) |
| Public sports data ("core") | `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/…`                                                 | v2      | Birthdates ⏳ (athlete ids are the same as fantasy player ids)                                                                                                                                   |
| Public site API             | `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/…` and `https://site.web.api.espn.com/apis/common/v3/…` | v2 / v3 | Not used yet; see the alternative below                                                                                                                                                          |

`{season}` is the year the season **ends** (2026-27 → `2027`).

**Alternative worth keeping in mind (raised in review):** ESPN's public sports
APIs (scoreboard, game summaries with box scores, athlete game logs, team
schedules) need no login and cover every NBA player with the same ids. They
could replace the fantasy API for _stats and schedule_, leaving the fantasy API
for _league_ data only. We're starting with the fantasy API because one batched
call per 50 players returns per-game stats plus ESPN's fantasy-point total as a
cross-check, which is efficient and self-verifying. The single-package design
means switching the stats source later is contained. The spike can probe one
scoreboard day as a cheap option check.

## 3. Authentication

- The league is private, so league views need two cookies, `espn_s2` and `SWID`,
  from the **bot ESPN account** (co-manager of the owner's team, no commissioner
  rights). League-independent calls need no cookies.
- Logging in programmatically is blocked by reCAPTCHA, so cookies are copied by
  hand ([runbook](devops.md#6-runbooks)) and expire occasionally.
- Prod: Secret Manager, readable only by the sync job. Laptop:
  `~/.config/hoops-dream/espn.env`, outside the repo.
- Never log, print, or commit cookie values. Never use the owner's personal
  cookies in the cloud.

## 4. What the sync fetches

| Data                       | Fantasy API view                     | Cookies | Notes                                                                    |
| -------------------------- | ------------------------------------ | ------- | ------------------------------------------------------------------------ |
| League settings            | `mSettings`                          | yes     | Scoring weights, lineup slots, matchup periods, playoffs, trade deadline |
| Teams and rosters          | `mTeam` + `mRoster`                  | yes     | Rosters on a past day via `scoringPeriodId` ⏳                           |
| Player pool with injuries  | `kona_player_info` (paged by 500)    | yes     | Rostered, free agents, waivers                                           |
| Per-game stats             | `kona_playercard` (≤50 ids per call) | yes     | Last 7 days normally; whole season on the first run ⏳                   |
| NBA schedule and team list | `proTeamSchedules_wl`                | no      | NBA team ids are mapped at runtime from this response; never hard-coded  |
| Active NBA players         | `players_wl`                         | no      | Name ↔ id map                                                            |
| Birthdates                 | core athletes endpoint               | no      | One call per new player ⏳                                               |
| Matchup scores (M7)        | `mMatchup` + `mMatchupScore`         | yes     | Verify and record a fixture first ⏳                                     |

Behavior: at most **1 request per second**; 3 retries with exponential backoff
and jitter on 429/5xx; 30 s timeout. A normal day is 20–40 requests; the first
run adds a few hundred birthdate calls (about 10 minutes), so the job timeout is
60 minutes. On 401/403 the job stops, records `espn_auth` in the status file,
and leaves the data as it was.

## 5. ESPN quirks to remember

- **Stat ids** for games started/played (41/42) and ejections/disqualifications
  (7/12) are disputed between sources, so games played is computed as "games
  with minutes > 0" and those ids aren't used.
- **Lineup slot ids** beyond 13 exist (14 unused, 15 a legacy "Rookie" slot).
  Unknown slot ids count as bench, with a warning.
- **Member ids are SWIDs**, i.e., half of a login cookie. The sync and the spike
  replace them with consistent fake GUIDs before writing anything to disk.
- Aggregate stat splits are prefixed `00` (season), `10` (projected), `01/02/03`
  (last 7/15/30 days); single-game splits carry a scoring period id.

## 6. Fixtures

A fixture set is one folder `backend/internal/espn/testdata/<date>/` holding the
spike's (or `make sync`'s) raw output as-is, with a `meta.json` (league id,
season, capture time, latest scoring period). `make replay` builds local data
from the newest set. Team and manager names remain, which is why the repo is
private. When ESPN changes shape, record new fixtures and fix the parser; never
loosen tests.

## Open facts

Confirmed by running the spike (`tools/spike/`) **before M3**; paste the report
into this doc under "Spike results" and resolve every ⏳ across the docs:

- [ ] Scoring weights match the FPTS formula
- [ ] Lineup slot counts (starters, bench, IR) and each player's eligible slots
- [ ] Matchup periods and playoff weeks; the trade deadline
- [ ] Whether ESPN honors `scoringPeriodId` for past rosters (if not, start a
      daily sync as early as possible)
- [ ] Per-game stats back to opening night, and what the "top N periods" filter
      means
- [ ] Birthdate coverage (rookies, two-way players)
- [ ] Whether per-game stats work without cookies (`leaguedefaults`)
- [ ] The time zone of a scoring period
- [ ] (Optional) one public scoreboard day, to evaluate the public-API
      alternative
