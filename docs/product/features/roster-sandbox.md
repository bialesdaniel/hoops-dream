# Roster sandbox

**Status:** Planned (M8)

> Naming: "sandbox" replaces the interview's "what-if". Alternatives considered: "move simulator", "trade lab",
> "mock moves". Rename freely; the behavior is the same.

## Problem

Today the owner tests a pickup or trade by retyping names on the sheet's Teams tab and watching values move.
Synced rosters can't be edited by hand, so the app needs a safe place to try moves. A good sandbox also catches a
trap the sheet can't: a trade for a *better* player can make a week *worse* when the new roster has more eligible
players than lineup slots on some days, which an additional move could fix.

## User stories

- As the owner, I want to add, drop, or trade players across any teams and immediately see how player values and
  projections change, so I can evaluate a move before proposing it.
- As the owner, I want to see the **change in projected points for each future week** and for the **season
  total**, so I know whether a move helps when it matters (especially the playoff weeks).
- As the owner, I want weeks flagged where the new roster has **positional problems**: days with more eligible
  players than slots they can fill, or players who can't all fit the lineup, so I notice when a trade for a better
  player would actually cost me points, and can fix it with another move.
- As the owner, I want to reset everything with one click, so experiments never pollute the real data.

## Acceptance criteria

- Sandbox mode can be turned on and off; when it's off, every page shows real data only.
- Moves: add a free agent to a team, drop a player, move a player between teams (a trade is two or more moves).
- Changed numbers show the **delta** against the real value; a full side-by-side view is not required.
- A per-week table shows, for the affected teams: projected points before, after, and the delta, for every future
  week and the season total, with playoff weeks highlighted.
- Each week shows a positional-pressure indicator (from [projections.md](projections.md)): the number of days where
  a candidate couldn't be placed in a slot and the projected points left on the bench. Weeks where pressure
  increased because of the moves are flagged.
- Nothing is saved. Reloading the page or resetting discards the moves. (Saved scenarios were considered and
  rejected for now.)
- Player stat metrics never change in the sandbox; only team membership, team-level numbers, and projections do.

## Out of scope
- Saved or shared scenarios.
- Suggesting the extra move that fixes a positional problem (a candidate for later).
- Future draft picks as trade assets (league hub).

## Design notes
- Engineering constraint that makes this cheap: player stats must never depend on rosters
  ([architecture.md](../../engineering/architecture.md)).
- Depends on projections (M7), which is why the sandbox comes after them.
- UI details are decided when this milestone starts.

## History
- 2026-10-26: created; per-week deltas and positional-pressure flags added after the owner's review.
