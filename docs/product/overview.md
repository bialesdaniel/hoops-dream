# Product Overview: hoops-dream

> **How the product docs fit together:** this overview holds the vision, goals,
> principles, and quality targets. [roadmap.md](roadmap.md) is the ordered list
> of milestones. Each feature or domain gets its own doc in
> [features/](features/README.md) with user stories and acceptance criteria.
> Those feature docs are the living requirements: they are updated whenever a
> feature changes.

## The problem

The owner runs a 16-team ESPN fantasy basketball league (head-to-head points,
dynasty-style). The decisions that matter most (pickups, trades,
playoff-schedule planning, long-term roster building, sizing up rivals) aren't
supported by ESPN's app, so the owner keeps a large Google Sheet. The sheet is
fragile and expensive to maintain:

- rosters are retyped by hand after every move
- stats come from basketball-reference via `IMPORTHTML`, which breaks often and
  needs babysitting
- the NBA schedule is pasted in as CSV
- weekly history is copied by hand

The sheet is kept as a behavior reference in
[`docs/reference/`](../reference/README.md). The app does **similar** things; it
is not a 1:1 port.

## Who it's for

| Phase | Users           | What they get                                                                                                                  |
| ----- | --------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Now   | The owner       | A private replacement for the sheet                                                                                            |
| Later | All 16 managers | A shared league hub: valuations visible to everyone, pick tracking, trade proposals with future picks, and a custom draft room |

## Goals

1. Replace the sheet with an app that needs **no manual upkeep**.
2. Support the decisions the sheet supports: waiver/free-agent pickups,
   evaluating trades, playoff-schedule planning, dynasty roster building and
   draft prep, and sizing up rivals.
3. Make it **easy to add new player and team metrics** over time.
4. Run **as close to $0/month as possible** on GCP.
5. Grow into the **league's shared hub**.
6. Follow **good software engineering discipline over quick hacks**. The owner
   is also using the project to go deeper on Go, Connect/protobuf, and GCP.

## Non-goals (for now)

- Daily start/sit lineup optimization (the owner doesn't use the sheet for it).
- Writing anything back to ESPN.
- Supporting other leagues as a product (test leagues are fine).
- Native mobile apps.
- Exact numeric parity with the sheet.
- An in-app formula editor.
- Payments or "premium" features (the role model only leaves room for them).

## Product principles

- **Trustworthy data.** Every page shows when the data was last refreshed, and
  warns when it's stale.
- **Desktop-optimized, phone-usable.** Design for the laptop; every page must
  still be usable on a phone from the start, because league-mates will mostly
  use phones later.
- **Similar, not identical.** Formulas start from the sheet's logic and may
  improve; [formulas.md](../engineering/formulas.md) is the source of truth.
- **Small, frequent releases.** Each milestone ships something the owner can
  use.

## Quality targets

**Modifiability comes first.** This product will evolve for years (new metrics,
new features, the league hub), so we avoid decisions that are hard to undo:
volatile parts are isolated (the ESPN adapter, the identity provider, the metric
registry), interfaces are standard (protobuf, OIDC, files), and the few one-way
doors are written down in [decisions.md](../engineering/decisions.md).

| Attribute            | Target                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Modifiability        | Adding a metric, a page, or a data source touches one place; one-way-door decisions are rare and documented          |
| Cost                 | As close to $0/month as possible; budget alerts at $1 and $5; no fixed-cost cloud resources                          |
| Data freshness       | Refreshed daily; "Data as of …" shown everywhere; a warning after 36 hours without a successful refresh              |
| Performance          | No hard targets. Pages should feel responsive; a few seconds on first load is fine. Optimize later if it bothers us. |
| Availability         | Best effort. If ESPN is down, show stale data with a warning rather than an error page.                              |
| Security and privacy | Sign-in required; only invited people get in; league data is never public; no secrets in the repo                    |
| Devices              | Optimized for desktop; usable on a phone                                                                             |
| Correctness          | Matches formulas.md, with worked examples as tests                                                                   |

## How requirements are written

Feature docs use **user stories** plus **acceptance criteria**:

> As a league manager, I want to see my projected points for every future week,
> with special focus on the playoff weeks, compared with every other team, so I
> know what roster moves I need to make to win those weeks.

Acceptance criteria are short, testable statements under each story. The
template is in [features/README.md](features/README.md).
