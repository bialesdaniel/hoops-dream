# Rosters

**Status:** Planned (M4)

## Problem

The sheet's Teams tab is retyped by hand after every move, and every other tab depends on it. Synced rosters remove
the single biggest chore.

## User stories

- As the owner, I want to see every team's current roster exactly as ESPN has it, grouped the way the league is
  organized (divisions), so I never retype a roster.
- As the owner, I want to see each player's position(s), age, and whether he is on IR, and (once M5 lands) his
  FPPG and EDSA, so I can judge a team at a glance.

## Acceptance criteria

- All 16 rosters appear, with the division and team names ESPN uses.
- Per player: name, position(s), NBA team, age, IR flag. **FPPG and EDSA columns are added to this page as part of
  M5**, when the stats exist.
- Usable on a phone: one team at a time.

## Out of scope
- Roster history (what a team looked like on a past date). Snapshots are stored from M3 on, so this can be added
  later without losing data.
- Editing rosters (M8, the sandbox).

## Design notes
- Data concepts: [data.md](../../engineering/data.md)
- The retired "R.E" roster slot from the sheet is not modeled.

## History
- 2026-10-26: created; trimmed after the owner's review (no lineup slots, no past dates).
