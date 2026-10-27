# hoops-dream

A companion web app for our ESPN fantasy basketball league. It replaces the
manual Google Sheet with synced rosters, player values, a roster sandbox for
testing moves, projections, and playoff planning.

**Status:** designed, not yet built. Coding agents start at
[AGENTS.md](AGENTS.md). Humans start with
[docs/product/overview.md](docs/product/overview.md) and
[docs/product/roadmap.md](docs/product/roadmap.md).

## Docs map

| Folder                            | Contents                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------- |
| `docs/product/`                   | Overview, roadmap (milestones), and one doc per feature with user stories                   |
| `docs/architecture/`              | Architecture, backend, frontend, data, ESPN, security, DevOps, testing, formulas, decisions |
| `docs/plans/`                     | Execution plans for multi-step work                                                         |
| `docs/reference/`                 | The original spreadsheet, for behavior reference only                                       |
| `backend/`, `frontend/`, `proto/` | Code (to come), each with its own `AGENTS.md` of coding conventions                         |
| `tools/spike/`                    | The ESPN feasibility script                                                                 |

## First steps (owner)

1. Run the ESPN spike ([tools/spike/README.md](tools/spike/README.md)) and copy
   its output folder into `backend/internal/espn/testdata/<date>/`.
2. Create the bot ESPN account, add it as co-manager of your team, and save its
   cookies in `~/.config/hoops-dream/espn.env` (outside the repo).
3. Push this folder to a **private** GitHub repo; copy `.env.example` to
   `.env.local`.
4. Create the identity-provider tenant and the GCP project with billing and
   budget alerts (details in
   [docs/architecture/devops.md](docs/architecture/devops.md) and
   [security.md](docs/architecture/security.md)).
5. Keep your admin `gcloud` configuration inactive while agents work.
6. Tell your coding agent: "Read AGENTS.md and plan milestone M1."
