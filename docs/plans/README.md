# Plans

Write **one plan per stage (or sub-slice)** before coding, in `docs/plans/active/<stage>-<slug>.md`. Move it to
`docs/plans/done/` when finished. A plan is a living document: update **Progress**, **Surprises**, and the
**Decision log** as you work, so any new session can pick up where the last one stopped.

Jetski and other tools may save plans elsewhere by default. **Always save plans here.**

## Template

```markdown
# Plan: <stage / slice name>

## Goal
One paragraph. Link the roadmap stage and its "done when" sentence.

## Scope
- In: …
- Out: …

## Steps
- [ ] 1. … (small, testable; each step ends with `make check` passing)
- [ ] 2. …

## Validation
Exact commands and expected results, e.g. `make check`, `make dev` → open /players, see N rows.

## Risks / open questions
- … (ask the owner before starting if a step requires an "Ask first" action from AGENTS.md)

## Progress
- YYYY-MM-DD: …

## Surprises
- …

## Decision log
- … (anything that changes docs/decisions.md must be proposed to the owner first)

## Outcome
Filled in when done: what shipped, what was deferred, and which docs were updated.
```
