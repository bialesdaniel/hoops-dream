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

## Spike Results

ESPN feasibility spike v1.1: season 2027, run 2026-10-27 03:43 UTC Cookies
provided: yes (values are never printed)

### 1. Access

- League: PRIVATE: no-cookie status 401; cookies work

### 2. League-independent data

- NBA schedule (no cookies): 30 teams; games per team 80–80; scoring periods
  1–174
- Scoring period 1 = ['2026-10-20']; periods spanning more than one US/Eastern
  date: 0 []
- `statsOfficial` flag on past games: 86/86 (in team-game rows)
- Active NBA players list (no cookies): 1099 players

### 3. League settings

- Status: first scoring period 1, latest 7, final 153, current matchup period 2
- Scoring type H2H_POINTS; weights vs sheet FPTS: PASS (identical)
- Lineup slots: PG×1, SG×1, SF×1, PF×1, C×1, G/F×1, F/C×1, UTIL×1, BE×4, IR×2
  (total 14); lineup lock: INDIVIDUAL_GAME
- Matchup periods: 21 (regular season 18); playoff teams 8; playoff matchup
  length 1; divisions 4
- Trade deadline: 2027-01-25 12:00 EST; veto votes 9; review hours 48
- Draft: type OFFLINE; keeper count 5; date 2026-10-18 19:15 EDT
- Acquisitions: limit -1; matchup limit 0.7142857142857143; waiver hours 24

### 4. Rosters and player pool

- Teams 16; roster sizes 12–14; members 21
- Rostered players by lineup slot: PG=16, SG=16, SF=16, PF=16, C=16, G/F=16,
  F/C=16, UTIL=16, BE=63, IR=20
- Past rosters: PASS (roster at scoring period 1 differs from today by 42
  players)
- Player pool: 1099 players (888 free agents/waivers); injuryStatus present on
  710

### 5. Per-game stats

- Per-game box scores: 1099 players fetched; 845 have game lines; 2949 game
  lines total; earliest scoring period 1 (season starts at 1)
- Coverage: game lines on 2949/2952 team game days (100%; DNPs and injuries
  lower this)
- FPTS oracle: the sheet's formula reproduces ESPN appliedTotal on 1161/1161
  game lines (100.0%)
- Stat-ID check: bench appearances with a 0 → stat41 638, stat42 0 ⇒ games
  started (GS) is probably stat41
- Stat keys seen: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
  18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
  37, 38, 39, 40, 41, 42, 43, 44]
- Prior season (2026) league data: PASS

### 6. Cookie-free fallbacks

- Per-game stats WITHOUT cookies (leaguedefaults endpoint): PASS (32 game lines
  for 5 players)
- Birthdates via ESPN core athletes API (no cookies): 5/5
  - Trey Murphy III: dateOfBirth=2000-06-18T07:00Z, age=26, experience=6
    (status 200)
  - Brandon Miller: dateOfBirth=2002-11-22T08:00Z, age=23, experience=4
    (status 200)
  - John Collins: dateOfBirth=1997-09-23T07:00Z, age=29, experience=10
    (status 200)
  - Taelon Peter: dateOfBirth=2002-02-27T08:00Z, age=24, experience=2
    (status 200)
  - Graham Ike: dateOfBirth=2002-08-03T07:00Z, age=24, experience=0 (status 200)

### 7. Verdict

- **League access:** PRIVATE (cookies required)
- **NBA schedule:** PASS
- **Scoring == sheet FPTS:** PASS
- **Trade deadline:** 2027-01-25 12:00 EST
- **Past rosters:** PASS
- **Per-game stats:** PASS (backfill from scoring period 1)
- **FPTS oracle:** 100.0% match
- **Prior season:** PASS
- **Stats without cookies:** PASS (32 game lines for 5 players)
- **Birthdates:** 5/5

### 8. Request log (≤1 request/second)

| #   | request                     | status | ms   | KB   | cookie |
| --- | --------------------------- | ------ | ---- | ---- | ------ |
| 1   | league_settings_nocookie    | 401    | 258  | 0    | n      |
| 2   | league_settings             | 200    | 170  | 4    | y      |
| 3   | pro_team_schedules_nocookie | 200    | 320  | 413  | n      |
| 4   | players_wl_nocookie         | 200    | 280  | 257  | n      |
| 5   | league_team_roster          | 200    | 539  | 2265 | y      |
| 6   | league_roster_first_sp      | 200    | 1363 | 2022 | y      |
| 7   | player_pool                 | 200    | 1246 | 5295 | y      |
| 8   | playercard_00               | 200    | 442  | 386  | y      |
| 9   | playercard_01               | 200    | 914  | 404  | y      |
| 10  | playercard_02               | 200    | 343  | 415  | y      |
| 11  | playercard_03               | 200    | 324  | 397  | y      |
| 12  | playercard_04               | 200    | 358  | 396  | y      |
| 13  | playercard_05               | 200    | 308  | 343  | y      |
| 14  | playercard_06               | 200    | 321  | 286  | y      |
| 15  | playercard_07               | 200    | 321  | 269  | y      |
| 16  | playercard_08               | 200    | 286  | 233  | y      |
| 17  | playercard_09               | 200    | 301  | 190  | y      |
| 18  | playercard_10               | 200    | 318  | 187  | y      |
| 19  | playercard_11               | 200    | 255  | 136  | y      |
| 20  | playercard_12               | 200    | 234  | 118  | y      |
| 21  | playercard_13               | 200    | 284  | 113  | y      |
| 22  | playercard_14               | 200    | 281  | 116  | y      |
| 23  | playercard_15               | 200    | 647  | 122  | y      |
| 24  | playercard_16               | 200    | 244  | 124  | y      |
| 25  | playercard_17               | 200    | 254  | 112  | y      |
| 26  | playercard_18               | 200    | 259  | 129  | y      |
| 27  | playercard_19               | 200    | 242  | 114  | y      |
| 28  | playercard_20               | 200    | 243  | 115  | y      |
| 29  | playercard_21               | 200    | 290  | 111  | y      |
| 30  | prior_season_2026           | 200    | 217  | 4    | y      |
| 31  | leaguedefaults_nocookie     | 200    | 211  | 28   | n      |
| 32  | core_athlete_4397688        | 200    | 221  | 5    | n      |
| 33  | core_athlete_4433287        | 200    | 129  | 5    | n      |
| 34  | core_athlete_3908845        | 200    | 160  | 5    | n      |
| 35  | core_athlete_4703421        | 200    | 134  | 5    | n      |
| 36  | core_athlete_4703396        | 200    | 359  | 4    | n      |

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
