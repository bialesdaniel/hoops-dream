# proto/AGENTS.md: API contract conventions

Read with the root `AGENTS.md`. The contract is the source of truth for what the
UI and API exchange.

## Packages

- `hoopsdeam.v1`: the API (services and messages the UI uses).
- `hoopsdeam.storage.v1`: the file formats the sync writes and the API reads.
  Never exposed to the UI.

## Rules

- `buf lint` with the STANDARD rules and `buf breaking` against `main` must pass
  (`make check`).
- **Field numbers are never reused or renumbered.** Removed fields are
  `reserved`.
- Enums have a zero value `*_UNSPECIFIED`.
- Every RPC declares its permission with the custom method option (e.g.,
  `option (hoopsdeam.v1.permission) = PERMISSION_LEAGUE_READ;`). The server test
  fails otherwise.
- Every league-scoped request carries `LeagueRef { league_id, season }`.
- Every response that returns data includes `DataStatus { data_as_of, stale }`.
- Metric values travel as columns:
  `MetricColumns { repeated string metric_ids; repeated Row rows }`, where a
  row's values are `optional double`, so "missing" is distinct from 0.
- Dates are `YYYY-MM-DD` strings; timestamps are `google.protobuf.Timestamp`.
- Changing a shipped contract (anything merged to `main`) requires asking the
  owner first.

## Generation

`make gen` runs `buf generate`: Go to `backend/gen`, TypeScript to
`frontend/src/gen`. Output is git-ignored; CI regenerates it.
