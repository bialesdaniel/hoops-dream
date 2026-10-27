# Player stats and values

**Status:** Planned (M5); custom windows in M9

## Problem

Finding pickups and comparing players means looking at production over different stretches (the season, the last
month) and at a value that accounts for age in a dynasty league. The sheet does this across six tabs with fragile
imports.

## User stories

- As the owner, I want to sort and filter every player in the league pool by fantasy production for this season
  and for the last 30 days, so I can spot free agents worth adding and players who are heating up or cooling off.
- As the owner, I want a single player value (EDSA) that blends youth and production, so I can compare players for
  dynasty purposes.
- As the owner, I want to filter to available players and/or rostered players, so I see the right pool for the
  decision I'm making.
- As an engineer, I want new metrics to be easy to add later, so the app can grow with the owner's analysis.

## Acceptance criteria

- Windows in M5: **this season** (default) and **last 30 days**.
- Columns include the raw window totals (games, minutes, shooting, rebounds, assists, steals, blocks, turnovers,
  points), **FPTS, FPPG, FPPM**, their percentile ranks, age, and EDSA, as defined in
  [formulas.md](../../engineering/formulas.md).
- Filters: available / rostered (either or both); position; NBA team; name search.
- Sort by any column; multi-column sort; column pinning and show/hide.
- The table handles the whole pool (about 500 rows) without paging limits.
- Missing values show as "—", never as 0.
- FPPG and EDSA also appear on the rosters page.
- Phone view: a short column set (name, team, FPPG, EDSA) with a tap-through to all metrics.

## Custom windows (M9)

- As the owner, I want to pick any stretch of the season (last N days, a date range, a single day), so I can look at
  specific runs of games.
- Acceptance: the same table and metrics work for any window within the current season; ranks are recomputed for
  the chosen window.

## Out of scope
- Last-season data (windows stay within the current season; decided in the interview).
- Team-level metrics (M10).

## Design notes
- Formulas: [formulas.md](../../engineering/formulas.md)
- Metric registry (how metrics are added): [backend.md](../../engineering/backend.md#the-metric-registry)

## History
- 2026-10-26: created; windows narrowed to season + last 30 days for M5 after the owner's review.
