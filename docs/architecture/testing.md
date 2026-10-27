# Testing

> What we test at each layer, why that layer exists, and how the owner verifies work by hand before it's committed.

## 1. Manual verification (before anything is committed)

The owner wants to see things work before code lands. So, for every change:

1. The agent finishes the work and runs `make check`.
2. The agent **stops before committing** and writes verification steps: what to run (usually `make dev`), which
   URL to open, what to click, and what the owner should see, plus any edge cases worth trying.
3. The owner follows the steps and either confirms or sends corrections.
4. Only after confirmation does the agent commit and open the PR. The PR description repeats the verification steps
   under "How to verify".

## 2. Automated layers

| Layer | What it checks | Why it exists | How |
|---|---|---|---|
| **Formula tests** | Every metric and projection rule against the worked examples in [formulas.md](formulas.md) | The numbers are the product; the examples are the spec | Table-driven Go tests, written **before** the code. Expected values are never edited to make a test pass. |
| **Metric registry tests** | Every metric has a worked example; ids never disappear; no dependency cycles | Protects the "new metric = one function" promise | Go tests over the registry |
| **ESPN parsing tests** | Our parsers against recorded ESPN responses | ESPN is unreachable from CI; recorded fixtures are the contract | Fixtures in `backend/internal/espn/testdata/`; retry and backoff behavior tested with a fake HTTP server |
| **Sync pipeline tests** | Replaying fixtures produces complete per-day files; a failed run leaves previously written files intact; the status file is written last and records errors | Data integrity | Temp-folder storage |
| **API tests** | Handlers return correct shapes; token verification rejects bad tokens; every RPC declares a permission; permission denial works | Security and contract | Go tests with locally minted tokens |
| **Frontend tests** | Components and hooks | Catch regressions in UI logic | Vitest + React Testing Library, with an in-memory API transport |
| **End-to-end smoke** (from M4) | `make dev` on fixtures → sign in (dev token) → the rosters page shows 16 teams | Catches wiring breaks across the stack | One Playwright test in CI |
| **Post-deploy smoke** | The new revision answers `/healthz` and serves the app before it takes traffic | The free substitute for staging | Part of the deploy workflow |
| **Security checks** | Known vulnerable dependencies; committed secrets | Supply chain hygiene | `govulncheck`, `pnpm audit`, gitleaks in `make check` |

## 3. Conventions

- `make check` runs everything CI runs. Run it before asking for verification.
- Tests live next to the code they test. Fixtures and worked examples are the only test data; no hand-typed
  expected values without a source.
- A bug fix starts with a failing test.
- Don't test implementation details (private functions, exact DOM structure); test behavior.
