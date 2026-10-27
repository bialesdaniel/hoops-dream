# Feature docs

One doc per feature or domain. A feature doc is the **living requirements** for that area: when a feature adds,
changes, or removes a requirement, its doc changes in the same PR. Pages are documented here as they are built.

## Status values

`Idea` → `Planned` (in a milestone) → `In progress` → `Shipped` → `Changed` (with a dated note)

## Template

```markdown
# <Feature name>

**Status:** Planned (M<n>) · **Owner:** <name>

## Problem
One short paragraph: what decision or chore this supports, and why ESPN's app or the sheet falls short.

## User stories
- As a <role>, I want <capability>, so that <benefit>.

## Acceptance criteria
Short, testable statements grouped by story. Mark unknowns `[open]` instead of guessing.

## Out of scope
What this feature deliberately does not do (yet).

## Design notes
Links to formulas, engineering docs, and the pages that implement it (added as they are built).

## Open questions
- …

## History
- YYYY-MM-DD: created / changed because …
```

## Writing tips

- One story per real decision the user makes. If a story has no "so that", it's probably not a user need.
- Acceptance criteria say *what*, not *how*. "Shows 'Data as of' on every page" is good; "uses a React context" is
  not.
- Keep numbers in [formulas.md](../../engineering/formulas.md) and link to them, so there is one source of truth.
