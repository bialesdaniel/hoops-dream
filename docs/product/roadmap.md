# Roadmap

> An ordered list of milestones, **no dates**. The owner drives the work and sends agents instructions milestone by
> milestone, so this list stays short. Details live in the linked feature docs. Each milestone has a one-line
> "done when".

| # | Milestone | Done when | Feature doc |
|---|---|---|---|
| M1 | **Walking skeleton:** the `web` and `api` services are deployed from CI, and a status page shows the API is healthy | "I open the URL and see a status page that talks to the API." | [foundation.md](features/foundation.md) |
| M2 | **Sign-in:** only invited users can get past the status page | "I sign in with Google; nobody else can." | [foundation.md](features/foundation.md) |
| M3 | **Daily ESPN sync:** league and player data refresh every morning; the status page shows "data as of" and sync health | "The status page shows this morning's refresh without me doing anything." | [foundation.md](features/foundation.md) |
| M4 | **Rosters:** all 16 teams as ESPN has them, with positions, age, and IR status | "I never retype a roster again." | [rosters.md](features/rosters.md) |
| M5 | **Player stats and values:** sortable, filterable player tables for **this season and the last 30 days**, with FPTS, FPPG, FPPM, ranks, and EDSA; values also appear on rosters | "I can find free agents and compare players without the sheet." | [player-values.md](features/player-values.md) |
| M6 | **Schedule planner:** games per NBA team, player, and fantasy team, per week and for the playoffs | "I see playoff-week game counts at a glance." | [schedule-planner.md](features/schedule-planner.md) |
| M7 | **Projections:** expected points for every future week, with special focus on the playoff weeks, using position-aware daily lineups | "I plan playoff moves in the app." | [projections.md](features/projections.md) |
| M8 | **Roster sandbox:** try adds, drops, and trades; see per-week and season deltas and positional problems, without saving | "I can test a trade without the sheet." | [roster-sandbox.md](features/roster-sandbox.md) |
| M9 | **Custom windows:** last N days, custom date ranges, single days | "I can look at any stretch of the season." | [player-values.md](features/player-values.md#custom-windows-m9) |
| M10 | **History and team dashboard:** weekly trends and team-level views (design to be decided) | "The sheet is retired." | [history-and-team-dashboard.md](features/history-and-team-dashboard.md) |
| Later | **League hub:** league-wide sign-in, pick tracking, trade proposals with future picks, custom draft room | Each designed when it starts | [league-hub.md](features/league-hub.md) |

Why this order: the schedule planner (M6) is an input to projections (M7), and the sandbox (M8) is most useful once
it can show projection deltas. M7 and M8 are worth most **before the league's trade deadline**.

## Before M1 (owner tasks)

- Run the ESPN spike (`tools/spike/`) and resolve the open facts in [espn.md](../engineering/espn.md#open-facts).
- Create the bot ESPN account and add it as co-manager of your team.
- Create the GCP project, billing, and budget alerts; create the Auth0 tenant (see
  [security.md §8](../engineering/security.md#8-choosing-the-identity-provider)).
