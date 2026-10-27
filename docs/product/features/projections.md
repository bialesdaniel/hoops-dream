# Projections

**Status:** Planned (M7)

## Problem

Winning a week is about how many points your lineup will actually score, given who plays on which days, who is
hurt, and which lineup slots each player can fill. The sheet approximates this with "top 8 by FPPG, positions
ignored". The app should do it properly: a position-aware lineup for each day.

## User stories

- As a league manager, I want to see my projected points for every future week, with special focus on the playoff
  weeks, compared with every other team, so I know what roster moves I need to make to win those weeks.
- As the owner, I want projections for the current week (points scored so far plus the rest of the week), each
  remaining week, and each playoff week, so I can plan short- and long-term.
- As the owner, I want projections to respect lineup slots and injuries, so they reflect what will really count.
- As the owner, I want to choose which stretch of games drives the projection (whole season, or recent games),
  so I can weigh current form.
- As the owner, I want sandbox moves (M8) reflected in projections, so I can evaluate trades for the playoffs.

## Acceptance criteria

- Per fantasy team and per period: current week (actual so far + projected remainder), **every** remaining week
  including each playoff week, and a rest-of-season total. Playoff weeks are visually distinguished.
- Weeks follow ESPN's matchup periods, including two-week periods.
- Each day's projected lineup is the **best legal lineup**: players are placed into the league's lineup slots
  according to their slot eligibility, maximizing projected points. Bench players don't count. The exact method is
  in [formulas.md §9](../../engineering/formulas.md#9-projected-fantasy-points).
- Each week also reports **positional pressure**: days when eligible players outnumber the slots they can fill,
  and the points left on the bench as a result. The sandbox (M8) uses this to flag trades that look better than
  they are.
- A player listed OUT is excluded until his expected return date.
- Players in IR slots are excluded unless "include IR" is turned on.
- The projection basis (per-game points over a chosen window: season by default, or recent N days) is selectable.
- The comparison view ranks all 16 teams for the selected period.

## Out of scope
- Game-level factors (opponent strength, back-to-backs, rest days).
- Automatic lineup setting in ESPN.

## Design notes
- Formulas: [formulas.md §9](../../engineering/formulas.md#9-projected-fantasy-points)
- Sandbox interaction: [roster-sandbox.md](roster-sandbox.md)

## Open questions
- `[open]` Default projection window: season, or something like the last 20 days? Start with season; make it a
  setting.

## History
- 2026-10-26: created; replaced the sheet's "top 8 by FPPG" with position-aware lineups per the owner's review.
