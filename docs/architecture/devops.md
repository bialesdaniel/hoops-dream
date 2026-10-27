# DevOps: infrastructure, CI/CD, operations

> How the cloud resources are created, how code gets deployed, how we know
> things are working, and what to do when they aren't. Each section explains the
> problem first.

## 1. Environments

| Environment            | What it is                            | Data                                                                                | Sign-in                                                            |
| ---------------------- | ------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **local** (`make dev`) | API and web dev server on your laptop | `./data`, built from recorded fixtures by `make replay`, or from a real `make sync` | The real identity provider, with `localhost` allowed as a callback |
| **production**         | One GCP project                       | The bucket                                                                          | The identity provider                                              |

There is **no staging environment**, to stay at $0 (Cloud Scheduler's free quota
is per billing account, and most of the value of staging is covered by the
no-traffic smoke test in §3).

## 2. Infrastructure as code (Terraform)

- **Problem.** Clicking resources together in the console isn't reproducible,
  and nobody remembers what was clicked.
- **What Terraform is.** A tool that reads files describing the desired cloud
  resources (`infra/*.tf`) and creates or updates them to match. The files are
  reviewed in PRs like code.
- **What's in it.** Enabled APIs, the bucket (versioning, lifecycle rules),
  Artifact Registry (where container images are stored, with a cleanup policy),
  the two Cloud Run services and the job, Cloud Scheduler, Secret Manager
  secrets (the containers, not the values), service accounts and their roles,
  and the Workload Identity Federation setup that lets GitHub Actions deploy
  without a stored key.
- **Who runs it, and why.** The **owner**, from the laptop (`terraform plan`,
  then `apply`). CI never runs Terraform, so the CI identity never needs
  project-admin rights. One-time setup: `infra/bootstrap.sh` creates the bucket
  where Terraform keeps its state.
- **Two details that avoid classic mistakes.**
  - Terraform creates secrets but never their _values_, so secrets never end up
    in Terraform's state file. Values are added once by the owner
    (`make rotate-espn-cookies`).
  - The Cloud Run resources ignore the container image field after creation.
    Otherwise every `terraform apply` would roll the services back to whatever
    image Terraform last knew about, undoing CI's deploys.
- Budget alerts ($1 and $5) are created by hand once, so CI never needs billing
  permissions.

## 3. CI/CD (GitHub Actions)

**On every pull request:** `make check` (format, lint, protobuf checks, code
generation, tests, vulnerability and secret scans). These jobs have **no cloud
credentials**; they only read the repo.

**On merge to `main`,** for each of `web`, `api`, and `sync`:

1. **Guard:** confirm the commit came from a merged pull request. (GitHub Free
   can't enforce branch protection on private repos, so this is the server-side
   check behind the local pre-push hook.)
2. **Build** the container image in Actions and push it to Artifact Registry.
3. **Deploy without traffic:** create a new Cloud Run revision tagged
   `candidate` that receives 0% of traffic.
4. **Smoke test** the candidate's own URL (`/healthz` and `/` for the API; `/`
   for the web app).
5. **Shift traffic** to the candidate. If the smoke test fails, nothing changed
   for users.

**Rollback** is one owner-run command that shifts traffic back to the previous
revision.

**Credentials:** Actions authenticates to GCP through Workload Identity
Federation, which trusts a token GitHub issues to the workflow. The trust is
restricted to **this repository and the `main` branch**, and the deploy service
account can only push images and update Cloud Run, nothing else.

**Cost controls in CI:** cancel superseded runs, skip jobs whose paths didn't
change, and keep within the free 2,000 minutes per month.

## 4. Knowing it works (monitoring at $0)

- **In the app:** every page shows "Data as of …" and a warning when stale. The
  owner uses the app daily, so this is the primary monitor.
- **`/statusz`:** the API reports freshness and the last sync error as JSON
  (HTTP 503 when stale).
- **Free alerting:** a scheduled GitHub Actions workflow runs every morning
  after the sync, requests `/statusz`, and fails on a non-200. GitHub emails the
  owner when a workflow fails. No paid alert policies.
- **Logs:** structured JSON to Cloud Logging (request id, user id, latency,
  status); Cloud Run job execution history; Error Reporting (free).

## 5. Cost guardrails

- Region `us-central1` only (free tiers apply there). Everything scales to zero;
  `max-instances=2` caps abuse.
- Never: load balancers or forwarding rules, `min-instances` > 0, always-on CPU,
  Cloud NAT, static IPs, Cloud SQL, Memorystore, any database service, resources
  outside `us-central1`. (Also in `AGENTS.md`.)
- Artifact Registry cleanup policy (old images), bucket lifecycle rules (`raw/`
  archive 400 days, noncurrent versions 30 days).

## 6. Runbooks

**Rotate the ESPN cookies** (when the status page reports an ESPN login
failure):

1. In a private browser window, log in to ESPN as the bot account and open the
   league.
2. Copy the `espn_s2` and `SWID` cookie values (DevTools → Application →
   Cookies). Close the window without logging out.
3. Update `~/.config/hoops-dream/espn.env`, then run `make rotate-espn-cookies`
   (owner only). It stores new secret versions, deletes the old ones, and
   triggers a sync.
4. Confirm the status page shows a fresh "Data as of".

**Re-run the sync by hand:** `gcloud run jobs execute sync --region us-central1`
(owner only).

**Roll back a deploy:**
`gcloud run services update-traffic <service> --to-revisions <previous>=100`
(owner only).

**Rebuild local data:** `make replay` (from fixtures) or `make sync` (live).

**Recover an overwritten file:** restore the previous object version in the
bucket (versioning is on).
