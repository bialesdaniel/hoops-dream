# backend/AGENTS.md: Go conventions

Read with the root `AGENTS.md`. Design: `docs/architecture/backend.md`.
Commands: `make help`.

## Layout

- Module `github.com/bialesdaniel/hoops-dream/backend`. Programs in `cmd/api`
  and `cmd/sync`; everything else under `internal/` so nothing is importable
  from outside.
- Package names are short nouns (`espn`, `ingest`, `storage`, `domain`,
  `metrics`, `projections`, `api`, `auth`). One responsibility per package; no
  `util` or `common`.
- Generated code goes to `gen/` (git-ignored). Never edit it; run `make gen`.

## Style

- `gofmt` and `golangci-lint` decide formatting and lint; don't argue with them
  in code review.
- Accept interfaces, return structs. Keep interfaces small and defined where
  they're used (e.g., `storage.Store`).
- Errors: wrap with context (`fmt.Errorf("load status file: %w", err)`); define
  sentinel errors for conditions callers branch on (e.g., `espn.ErrAuth`). Never
  swallow errors; never `panic` in library code.
- Context first: every I/O function takes `ctx context.Context` as its first
  parameter and respects cancellation.
- Logging: `log/slog`, structured, with a request id. Never log tokens, cookies,
  or emails.
- Configuration comes from environment variables, read once in `cmd/*` and
  passed down as a struct.
- Time: store and compute in UTC; convert at the edges. Dates as `YYYY-MM-DD`
  strings in APIs and files.
- Money/precision: compute in `float64`, round only for display.

## Domain rules in code

- `internal/espn` is the only package that may mention ESPN field names or ids.
- Player statistics never depend on rosters.
- Metrics live in `internal/metrics` as registered functions with a
  worked-example test each.

## Testing

- Table-driven tests; `testdata/` folders for fixtures; `t.TempDir()` for
  storage; no network.
- Name tests after behavior (`TestEDSA_UnknownAgeUsesZeroFactor`), not after
  functions.

## Pre-approved dependencies

`connectrpc.com/connect`, `connectrpc.com/cors`, `github.com/rs/cors`,
`google.golang.org/protobuf`, `github.com/coreos/go-oidc/v3`,
`cloud.google.com/go/storage`, `cloud.google.com/go/secretmanager`,
`gopkg.in/yaml.v3`. Tools: `buf`, `protoc-gen-go`, `protoc-gen-connect-go`,
`golangci-lint`, `govulncheck`. Anything else: ask first.
