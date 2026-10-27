# League hub

**Status:** Idea (after M10). Each part is designed when it starts.

## Vision

The app becomes the league's shared tool, with valuations visible to everyone.

## Parts

| Part | Notes |
|---|---|
| League-wide sign-in | Invite the 15 other managers; per-league roles (admin, member); each user linked to their fantasy team |
| Pick tracking | Import the owner's draft-pick ownership sheet; the app becomes the system of record for future picks, so it needs a real database and backups |
| Trade proposals | Proposals that include players and future picks; accept/decline; history |
| Custom draft room | The league's format can't be run in ESPN. Real-time, multi-user; the transport is chosen then. Test leagues allow rehearsals. |
| Personal metric presets | Per-manager weights for valuations |

## Things decided early so this stays possible

- Player identity is internal with ESPN ids as external keys, so prospects without ESPN ids fit later.
- Metric weights are versioned parameters, not constants.
- League data is keyed by `(league_id, season)`, so test leagues work.
- User identity is keyed by our own id once we store per-user data, not by the identity provider's id.

## Open questions
- Database choice when user-entered data arrives (see [data.md §6](../../engineering/data.md#6-when-we-need-a-database)).
- Whether valuations use one league formula or per-manager weights.
