# Security

> Who could attack what, and the controls we use. Each control says **why** it
> exists. The identity-provider choice is at the end with its tradeoffs.

## 1. What we're protecting, and from whom

| Asset                             | Threat                                                              | Control                                                                                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| League data (rosters, valuations) | Strangers reading it from a public URL                              | Sign-in required; invite list; every RPC checks a permission                                                                                                             |
| The bot ESPN account              | Its cookies leaking, letting someone make moves on the owner's team | Cookies only in Secret Manager and a file outside the repo; never logged or committed; scrubbed from recorded fixtures; least-privilege account (no commissioner rights) |
| The cloud project                 | Runaway cost or destructive changes                                 | Budget alerts; fixed-cost resources banned; owner-only infrastructure changes; CI can only deploy app code                                                               |
| The repository                    | Malicious or careless changes shipping                              | CI checks on every PR; the deploy workflow only ships merged PRs; owner's manual verification; dependency and secret scanning                                            |
| The owner's laptop                | AI agents touching credentials or cloud resources                   | Tool deny-lists; cookies outside the repo; admin `gcloud` config inactive by default                                                                                     |

## 2. Sign-in and tokens

- **Who you are** is proven by a managed identity provider: the browser app
  sends the user to the provider's sign-in page (Google account first; more
  methods later) and receives a short-lived **access token** for our API.
- **Every API call** carries that token. The API verifies the signature with the
  provider's published public keys, plus the issuer, audience, and expiry. No
  session state exists on our side, so instances can scale freely.
- **Invite list:** sign-ups are disabled; the provider denies anyone not invited
  (a post-login rule). Removing a person takes effect when their current token
  expires (minutes), with no deploy.
- **Tokens in the browser** live in memory and are refreshed silently by the
  SDK. The main risk is cross-site scripting, which is why the headers below
  matter.

## 3. Access control (what you can do)

- Permissions are coarse: `authenticated`, `league.read`, `league.admin`,
  `app.admin`. Roles map to permissions: `member` → read; `admin` → read +
  league admin; the owner is `app.admin`.
- **Every RPC declares its required permission** in the protobuf definition. An
  interceptor enforces it, denying by default, and a test fails if any RPC lacks
  a declaration. This stops "forgot to add auth" bugs.
- Roles come from token claims now (set in the provider). When the league hub
  needs per-league, per-team roles, they move to our own database keyed by our
  own user id, so a provider change never loses anyone.
- Resource-level checks ("your own team only") live in the handlers that need
  them.

## 4. Browser-side protections (why those headers)

Browsers enforce rules the server declares. These cost nothing and close common
attacks:

| Header                            | What it prevents                                                                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `Content-Security-Policy`         | Scripts or connections from anywhere but our own origins, which is the main defense against injected scripts stealing tokens |
| `Strict-Transport-Security`       | Downgrade to plain HTTP                                                                                                      |
| `X-Content-Type-Options: nosniff` | Browsers guessing a file type and executing something they shouldn't                                                         |
| `Referrer-Policy`                 | Leaking URLs to third parties                                                                                                |
| `frame-ancestors 'none'`          | Clickjacking (our app embedded invisibly in another site)                                                                    |

The CSP is never loosened to make something work; if something breaks, fix the
cause or ask the owner.

## 5. Cross-origin calls

The web app and the API have different origins, so the API sends CORS headers
allowing **only the web app's origin**, the headers Connect needs, and
credentials off (tokens travel in a header, not cookies). Health endpoints are
the only unauthenticated routes.

## 6. Secrets and cloud identity

- The only application secret is the bot's ESPN cookies, held in Secret Manager
  and readable only by the sync job's service account. The API needs no secrets
  at all (it verifies tokens with public keys).
- Cloud resources are created by Terraform **run by the owner**; CI deploys
  container images through Workload Identity Federation (no stored keys),
  restricted to this repository's `main` branch. Pull-request jobs have no cloud
  credentials.
- Separate service accounts for `api`, `sync`, and the deploy pipeline, each
  with the minimum roles.

## 7. Supply chain and code hygiene

- Dependencies pinned (`go.sum`, lockfile); GitHub Actions pinned by commit SHA;
  Dependabot weekly.
- `make check` runs `govulncheck`, `pnpm audit`, and gitleaks (secret scanning).
- Container images: multi-stage builds, distroless base, non-root.
- Logs never contain tokens, cookies, or emails.

## 8. Choosing the identity provider

The owner asked for the tradeoffs of Auth0 and similar services versus writing
sign-in into the Go API.

|                             | **Managed provider** (Auth0, WorkOS AuthKit, Clerk)                                                                                                                       | **Sign-in code in our API** (Google OIDC + our sessions)                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Security code we own        | ~50 lines (token verification)                                                                                                                                            | ~300 lines (OAuth flow, sessions, cookies, key rotation) plus the tests to prove it |
| Separate UI/API deployables | Natural: tokens in headers                                                                                                                                                | Awkward: cookies need one site, forcing a shared domain                             |
| User management             | Dashboard: invite, remove, roles, multiple sign-in methods                                                                                                                | Our own users file or database                                                      |
| Vendor dependence           | Yes. Free tiers: Auth0 25k monthly users, WorkOS 1M, Clerk 50k. Terms can change; swapping providers is possible because OIDC is standard, but it means re-linking users. | None beyond Google                                                                  |
| Sign-in page                | On the provider's domain (a custom domain is possible; Auth0 asks for a card on file for it)                                                                              | Google's consent screen, then back to us                                            |
| Learning value              | OIDC/JWT concepts, less plumbing                                                                                                                                          | Deepest, but it's plumbing                                                          |
| Cost                        | $0 at our scale                                                                                                                                                           | $0                                                                                  |

**Downsides of Auth0 specifically:** another account and dashboard to maintain;
the free plan omits some enterprise features we don't need (and some we might
like later, such as enforced MFA, which may need a paid plan); user records live
with Auth0; occasional free-tier changes (the last one made it more generous).
None of these matter at 16 users.

**Decision: Auth0.** Setup (owner, before M2): create a free tenant; add a
_Single Page Application_ (allowed callback, logout, and web origins = the web
app's URLs plus `http://localhost:5173`); add an _API_ with identifier
`https://api.hoops-dream` (this becomes the token audience); enable the Google
social connection and disable database sign-ups; add a post-login Action that
denies anyone whose email isn't on the invite list and adds roles to the token
as a custom claim. The API verifies tokens against the tenant's issuer and that
audience.
