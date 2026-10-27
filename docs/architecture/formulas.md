# Formulas and Glossary

> **Source of truth for every number the app shows.** Similar to the original sheet, not identical. Every metric
> has a worked example, and each example becomes a unit test. "FPTS" always means **fantasy points**, never NBA
> points (`PTS`). ⏳ = confirm after the ESPN spike.

## 1. Glossary

| Term | Meaning |
|---|---|
| Scoring period / day | One NBA game day, as ESPN numbers them (opening night = 1). ⏳ US/Eastern date |
| Matchup period / week | A fantasy week: an ordered list of days from ESPN's settings. Some periods span two calendar weeks (2026-27, per the sheet: Nov 30–Dec 13 and Feb 15–28 ⏳). Never derived from calendar Sundays. |
| Playoff weeks | The matchup periods after the regular season (2026-27: weeks 19–21, Mar 8–28 ⏳) |
| Window | The date range player stats are aggregated over: this season (default), the last N days, a custom range, or a single day. **Always within the current season.** |
| Lineup slots | The starting positions a league defines (e.g., PG, SG, SF, PF, C, G, F, UTIL), from ESPN settings ⏳. Bench and IR are not lineup slots. |
| Eligible slots | The lineup slots a given player may fill, from ESPN |
| EDSA | The player value score. The name is kept from the sheet. |
| Sandbox | Throwaway roster edits (add, drop, trade) applied to one request only; never saved |
| Metric | Any number computed per player or per team and registered in the metric registry (§11) |

## 2. Fantasy points (FPTS) per game

`FPTS = PTS + REB + AST + STL + BLK − (FGA − FGM) − (FTA − FTM) − TO`

The weights come from the league's ESPN scoring settings ⏳, so a scoring change carries over automatically.

**Cross-check:** ESPN also computes each game's fantasy points itself (the `appliedTotal` field). Our FPTS from the
box score must equal ESPN's number for every game; the sync warns when it doesn't. This is a free correctness test
of both our formula and our parsing.

| Example | MIN | FGM | FGA | FTM | FTA | REB | AST | STL | BLK | TO | PTS | **FPTS** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Player A | 31 | 12 | 21 | 7 | 8 | 5 | 3 | 5 | 0 | 3 | 38 | **38** |
| Player B | 36 | 13 | 27 | 3 | 4 | 6 | 4 | 3 | 3 | 2 | 32 | **31** |

## 3. Window aggregates

For each player, sum the per-game lines inside the window: G (games with minutes > 0), MIN, FGM, FGA, FTM, FTA,
REB, AST, STL, BLK, TO, PTS, FPTS.

- `FPPG = FPTS / G` (fantasy points per game). Missing if G = 0.
- `FPPM = FPTS / MIN` (per minute). Missing if MIN = 0.
- Percentages are **ratios of sums** (`FG% = ΣFGM / ΣFGA`), never averages of per-game percentages.
- Stats follow the player across NBA trades; the current NBA team matters only for the schedule.

Example, Player A over one game: FPPG = 38/1 = **38.0**, FPPM = 38/31 = **1.23**. Player B: FPPG = **31.0**,
FPPM = 31/36 = **0.86**.

## 4. Percentile ranks (0–100)

For a metric *m* (total FPTS, FPPG, FPPM) and the **population** P = players in the league's player pool (rostered,
free agents, waivers) with MIN > 0 in the window:

`rank(x) = 100 × |{p ∈ P : m(p) < m(x)}| / (|P| − 1)`

This is the spreadsheet function `PERCENTRANK.INC`. Ties get the same rank. If |P| = 1, the rank is 100. Players
outside P have a missing rank.

Example, values [10, 20, 20, 40] → ranks **0, 33.3, 33.3, 100**.

## 5. Age

Age is **decimal years** on **Feb 1 of the season's end year** (2026-27 → 2027-02-01), from the ESPN birthdate ⏳:

`age = days between birthdate and Feb 1 ÷ 365.25`, shown with 2 decimals.

| Birthdate | Age on 2027-02-01 |
|---|---|
| 1998-11-01 | 28.25 (28 years, 3 months) |
| 1998-10-01 | 28.34 (28 years, 4 months) |
| 2005-01-31 | 22.00 |
| 2005-02-02 | 22.00 (one day short of 22 rounds to 22.00) |

Why Feb 1: it matches basketball-reference's convention, so ages line up with the sheet, and it keeps a player's age
fixed for the whole season. **Default when the birthdate is unknown:** age is missing and the UI shows an "age
unknown" flag; EDSA then treats the age factor as 0 (§6).

## 6. Player value (EDSA)

EDSA combines youth and production. It is the weighted sum of an **age factor** and the three percentile ranks.

**Age factor** (used only by EDSA): 100 for anyone 22 or younger, 0 for anyone 32 or older, and a straight line in
between: `age_factor = (32 − age) × 10` for 22 < age < 32.

| Age | 20.0 | 24.5 | 27.0 | 31.0 | 36.0 | unknown |
|---|---|---|---|---|---|---|
| Age factor | 100 | 75 | 50 | 10 | 0 | 0 |

**Weights** (version 1; stored as versioned parameters, not constants):

| Input | Weight |
|---|---|
| Age factor | 0.64 |
| FPTS rank | 2.00 |
| FPPG rank | 3.86 |
| FPPM rank | 1.25 |

`EDSA = 0.64 × age_factor + 2 × fpts_rank + 3.86 × fppg_rank + 1.25 × fppm_rank` (maximum 775). Missing if any
rank is missing.

| Example | Age factor | FPTS rank | FPPG rank | FPPM rank | **EDSA** |
|---|---|---|---|---|---|
| Age 36, top in all ranks | 0 | 100 | 100 | 100 | 0 + 200 + 386 + 125 = **711.0** |
| Age 28.0 | 40 | 98.5 | 98.5 | 86.6 | 25.6 + 197 + 380.21 + 108.25 = **711.1** |

## 7. Team strength

**To be designed** (see [history-and-team-dashboard.md](../product/features/history-and-team-dashboard.md)). The
sheet's spreadsheet-shaped formula is intentionally not carried over.

## 8. Roster profile

Removed for now; may return with the team dashboard.

## 9. Projected fantasy points

**Idea:** for each remaining day, build the best legal lineup from the players who can actually play, add up their
expected points, and sum the days in each fantasy week.

**Inputs:** rosters (plus any sandbox edits), the NBA schedule, injuries, the league's lineup slots and each player's
eligible slots ⏳, an "include IR" toggle (default off), the as-of date, and a **projection basis**: each player's
FPPG over a chosen window (default: this season; the owner may prefer something like the last 20 days, so it's a
setting).

**Step 1: candidates for day d.** A player is a candidate if he is on the roster, not in an IR slot (unless include
IR is on), his NBA team plays on d, and he is not OUT on d. *OUT* means ESPN status OUT with no expected return
date, or a return date after d. **Default:** an OUT player with no return date is excluded for all remaining days.

**Step 2: fit candidates into lineup slots.** This is a small assignment problem: each lineup slot takes at most one
player, each player fills at most one slot, and a player may only take a slot he is eligible for. Choose the
assignment that **maximizes total projected FPPG**. Unfilled slots score 0; bench and IR never score.

- Solve it exactly. The sizes are tiny (at most ~13 slots and ~14 players), so a standard maximum-weight bipartite
  matching (or even exhaustive search) is instant.
- Why not greedy? Putting the best player in the first slot he fits can block a more specialized player. Example:
  slots G and UTIL; players A (eligible G or UTIL, 30 FPPG), B (UTIL only, 29), C (G or UTIL, 28). Greedy that
  drops A into UTIL leaves B out: 30 + 28 = 58. The best lineup is A→G, B→UTIL = **59**.
- Ties: prefer the lineup that uses more-specific slots for more-specific players; then lower player id. Any fixed
  rule is fine as long as it's deterministic.

**Step 3: positional pressure (per day, summed per week).** After fitting the lineup, record:
- *unplaced candidates*: candidates who could play that day but got no slot;
- *bench points*: the sum of their projected FPPG.

A week's pressure = the number of days with unplaced candidates, and the total bench points. The sandbox flags
weeks where pressure increased because of a move. In the example below, day 1 has one unplaced candidate if a
fourth eligible player were added (3 slots, 4 candidates).

**Step 4: periods.**
- **Current week** = ESPN's official team points for completed days **plus** day projections for the remaining
  days (today counts as remaining).
- **Each future week** and **each playoff week** = the sum of its day projections.
- **Rest of season** = the sum of all remaining regular-season days.

**Worked example** (lineup slots: G, F, UTIL; projection basis = season FPPG):

| Player | Eligible | FPPG | NBA team | Status |
|---|---|---|---|---|
| P1 | G, UTIL | 40 | X | healthy |
| P2 | G, UTIL | 30 | Y | healthy |
| P3 | F, UTIL | 20 | X | healthy |
| P4 | F, UTIL | 35 | Z | OUT, returns day 2 |

- Day 1 (X, Y, Z play): candidates P1, P2, P3 (P4 is OUT). Best lineup: P1→G, P3→F, P2→UTIL = **90**.
- Day 2 (X, Z play): candidates P1, P3, P4. Best lineup: P1→G, P4→F, P3→UTIL = **95**.
- Two-day total: **185**. Without the OUT rule, day 1 would have been P1→G, P4→F, P2→UTIL = 105.

## 10. Playoff-week game counts

| Count | Definition |
|---|---|
| Player | Scheduled games of his NBA team in each playoff week; injury status shown alongside |
| Team, player-games | The sum of those scheduled games over the team's non-IR players (availability ignored) |
| Team, usable games | Day by day, the number of lineup slots the day's candidates (§9 step 1) can fill, summed over the week. Games that can't fit a slot don't count. |

Example from §9, over the two days: scheduled player-games = P1 2 + P2 1 + P3 2 + P4 2 = **7**. Usable games: day 1
fills 3 slots, day 2 fills 3 slots → **6**.

## 11. Metric registry conventions

§2–6 and the player playoff count are registry metrics (design in
[backend.md](backend.md#the-metric-registry)). Projections (§9) and team counts (§10) are typed outputs of their own
RPCs. Team metrics will be added with the team dashboard.

**Golden list of metric ids** (append-only; a test enforces it):

| Group | IDs |
|---|---|
| Raw window sums | `g`, `min`, `fgm`, `fga`, `ftm`, `fta`, `fg3m`, `fg3a`, `reb`, `oreb`, `dreb`, `ast`, `stl`, `blk`, `to`, `pts` |
| Ratios | `fg_pct`, `ft_pct`, `fg3_pct` |
| Value | `fpts`, `fppg`, `fppm`, `fpts_rank`, `fppg_rank`, `fppm_rank`, `age`, `edsa` |
| Schedule | `playoff_games` |

Rules:
- Changing a metric's meaning requires a **new id** (e.g., `edsa_v2`). Adding a metric is a code change plus a
  worked example.
- Weights (EDSA weights, the age bounds 22/32) are **versioned parameters** in a config file, not constants.
- **Display:** FPTS as an integer; FPPG with 1 decimal; FPPM with 2; ranks and EDSA with 1; age with 2. Compute in
  float64 and round only for display. Missing shows as "—", never 0.
