# Reference: the original Google Sheet

`original-sheet-2026-10-25.xlsx` is an export of the owner's sheet: 25 tabs, with formulas plus cached values. It
is a **behavior reference only**. The app does *similar* things, as specified in [formulas.md](../engineering/formulas.md),
and is **not** expected to match these numbers. The export contains league members' names, so keep the repo
private.

| Sheet tab(s) | What it did | App equivalent |
|---|---|---|
| Player / Day Range / Daily Raw Data | `IMPORTHTML` from basketball-reference (season, last N days, single day) | ESPN per-game stats + windows |
| Player / Day Range / Daily Format Data | FPTS, FPPG, FPPM, percentile ranks, EDSA | Metric registry ([formulas.md](../engineering/formulas.md)) |
| Player / Day Range / Daily Sortable, Free Agents | Sortable views; unrostered players | Players page |
| Teams | Hand-typed rosters by division, with values | Teams page (synced from ESPN) |
| Schedule CSV / Raw / Daily / Weekly / Playoffs | Pasted NBA schedule → games per team per day and week | ESPN schedule → Schedule page |
| Matchup Daily / Season / Playoffs | Top-8-by-FPPG daily projections | Matchups page (with the OUT rule, ESPN matchup periods) |
| Current Roster Score v3 | Team strength rank, roster profile, Methuselah | Rankings page (Methuselah dropped) |
| Weekly EDSA | Manually copied weekly history + chart | Trend, computed from daily roster snapshots (fresh this season) |
| Global Variables | Roster sizes (14 / 8 / 2 / 12) | ESPN `lineupSlotCounts` (the R.E slot is retired) |

**Known sheet quirks the app intentionally does not copy:**
- It derives weeks from Sundays that have games, which gets the 2-week matchup periods right only by coincidence.
- It matches players by name string.
- It hard-codes roster sizes.
