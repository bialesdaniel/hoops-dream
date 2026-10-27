# Schedule planner

**Status:** Planned (M6)

## Problem

In the playoffs, the number of games a player's NBA team has in a given week matters as much as his averages. The
sheet rebuilds this from a pasted CSV; the app should derive it from ESPN's schedule automatically.

## User stories

- As the owner, I want to see how many games each NBA team plays in each fantasy week, especially the playoff
  weeks, so I can target players with favorable schedules.
- As the owner, I want to see each player's and each fantasy team's playoff-week game counts, so I can compare
  rosters on schedule alone.
- As the owner, I want "usable" games per team (games that fit into lineup slots), so I don't overvalue a deep
  bench.

## Acceptance criteria

- A grid of NBA teams × fantasy weeks with game counts; playoff weeks highlighted; two-week periods labeled.
- Per player: games in each playoff week (shown on the player table too).
- Per fantasy team: total player-games and usable games per playoff week, as defined in
  [formulas.md §10](../../engineering/formulas.md#10-playoff-week-game-counts).
- Reflects sandbox moves once the sandbox exists (M8).

## Out of scope
- Historical schedules from past seasons.

## History
- 2026-10-26: created.
