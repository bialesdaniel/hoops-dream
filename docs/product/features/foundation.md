# Foundation: status page, sign-in, daily sync

**Status:** Planned (M1–M3)

## Problem

Before any league feature can exist, three things must be true: the app is deployed and observable, only invited
people can use it, and league data refreshes itself. Doing these first, as the smallest possible slice, proves the
whole path (code → CI → cloud → browser) before anything complicated is built.

## User stories

### M1: Status page
- As the owner, I want a page that shows whether the app and the API are up, so I know the deployment works.
- As the owner, I want every merge to `main` to deploy automatically, so I never deploy by hand.

### M2: Sign-in
- As the owner, I want to sign in with my Google account, so nobody else can see league data.
- As the owner, I want to invite specific people later by email, so the league can join without a redesign.

### M3: Daily sync
- As the owner, I want league settings, rosters, player stats, injuries, and the NBA schedule refreshed every
  morning, so I never update anything by hand.
- As the owner, I want to see when the data was last refreshed on every page, and a warning when it's stale, so I
  can trust what I'm looking at.

## Acceptance criteria

**Status page (M1)**
- The page is public and shows: app version, API reachable (yes/no), and from M3 on, "Data as of <time>" and the
  last sync result.
- It never shows league data or anything sensitive.

**Sign-in (M2)**
- Every page except the status page requires sign-in.
- A signed-in person who isn't on the invite list is told "You don't have access yet" and sees nothing else.
- Removing someone from the invite list locks them out within minutes.

**Daily sync (M3)**
- Runs once a day without intervention; can also be run by hand.
- A failed run never damages the data being served; the app keeps showing the last good data, marked stale.
- If ESPN rejects the bot account's login, the status page says so (so the owner knows to refresh the cookies).
- Stat corrections ESPN makes within a week are picked up.

## Out of scope
- Any league page. M4 starts those.
- Alerts by email beyond the free GitHub-based check described in [devops.md](../../engineering/devops.md).

## Design notes
- Architecture: [architecture.md](../../engineering/architecture.md)
- Sign-in and access control: [security.md](../../engineering/security.md)
- Sync pipeline: [backend.md](../../engineering/backend.md#the-sync-pipeline), ESPN details: [espn.md](../../engineering/espn.md)

## Open questions
- None. (Identity provider: Auth0, decided 2026-10-26.)

## History
- 2026-10-26: created from the design interview.
