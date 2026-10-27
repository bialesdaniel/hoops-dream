# History and team dashboard

**Status:** Idea (M10). **Design to be decided.**

## Problem

The sheet tracked a weekly "team strength" score and chart by copying numbers every week, and it computed team
rankings in a way that suited a spreadsheet. The owner wants team-level views in the app but will design them
differently, and not first.

## What we know so far

- The daily sync stores a roster snapshot every day from the moment it goes live (M3), so any team-level metric can
  be computed **retroactively** for any past day once it's defined. No history is lost by deferring this feature.
- History starts this season; the sheet's old history is not imported (decided in the interview).
- Candidate ideas: a team ranking by total player value, a weekly trend chart, roster profile (positions, average
  age, number of NBA teams), and comparison against rivals.
- Any team metric must be addable through the metric registry
  ([backend.md](../../engineering/backend.md#the-metric-registry)).

## Open questions
- Which team-level numbers actually help decisions?
- Which charts?

## History
- 2026-10-26: created as a placeholder; the sheet's team-strength formula was intentionally not carried over.
