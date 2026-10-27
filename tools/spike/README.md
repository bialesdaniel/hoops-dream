# ESPN feasibility spike

`espn_spike.py` is a read-only script that uses only the Python 3.9+ standard
library. Run it **before Stage 0a**, on a machine that can reach ESPN.

```bash
set -a; source ~/.config/hoops-dream/espn.env; set +a   # ESPN_S2=... / ESPN_SWID=... (outside the repo)
python3 tools/spike/espn_spike.py --league-id <LEAGUE_ID> [--season 2027] [--fa-sample 0]
```

- It first tries without cookies, to detect a public league, then with the
  cookies from the env vars. Cookie values are never printed.
- By default it fetches per-game stats for **every** rostered player and free
  agent (`--fa-sample 0`).
- Outputs go to `espn_spike_out/<timestamp>/`, which is git-ignored:
  - `report.md`: redacted; paste it into
    [docs/architecture/espn.md](../../docs/architecture/espn.md) under "Spike
    results"
  - `raw/`: `<label>.json.gz` responses plus `meta.json`. **SWIDs are scrubbed
    on write**, replaced by consistent fake GUIDs. Copy this folder as-is to
    `backend/internal/espn/testdata/<yyyy-mm-dd>/` to create a fixture set for
    `make replay`. Team and display names remain, so keep the repo private.
