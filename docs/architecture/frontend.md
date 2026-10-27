# Frontend

> The `web` service: a React single-page app served as static files. Coding conventions live with the code in
> [`frontend/AGENTS.md`](../../frontend/AGENTS.md). Pages are documented in their feature docs as they are built.

## Stack and why

| Choice | Why |
|---|---|
| React + TypeScript + Vite | The owner's choice; mainstream, fast builds, well known to agents |
| MUI (Material Design components) | Material Design was a given; MUI is the standard React implementation (Material 2 with partial Material 3 styling) |
| Material React Table | Free, unlimited rows, column pinning, multi-sort. The MUI X grid's free tier caps pages at 100 rows and charges for pinning. |
| MUI X Charts (free tier) | Charts in the same design system |
| TanStack Query | Caching and loading states for API calls |
| React Router | Page routing |
| `connect-es` (generated client) | Typed calls to the API from the protobuf contract |
| Auth0 React SDK (`@auth0/auth0-react`) | Sign-in, token handling, and silent renewal without custom code |

## How the app talks to the API

1. On load, the identity provider SDK checks for an existing session and obtains an access token for our API.
2. A Connect interceptor attaches `Authorization: Bearer <token>` to every call.
3. Responses include `data_as_of` and `stale`; a global banner shows them.
4. On `unauthenticated`, the app redirects to sign-in; on `permission_denied`, it shows "You don't have access yet".

## Hosting

- The production build is a folder of static files with hashed names. A minimal container (nginx or Caddy) serves
  it on Cloud Run: unknown paths fall back to `index.html` (so deep links work), hashed assets are cached for a
  year, `index.html` is never cached, and security headers are set (see [security.md](security.md)).
- Why Cloud Run for static files: it keeps everything in GCP at $0 and scales to zero. The folder could move to
  any static host later without code changes.

## Principles

- **Optimized for desktop, usable on a phone** from the first page: responsive layouts, no horizontal scrolling
  for core actions, tap targets ≥ 44 px.
- **Build columns from the metric catalog** where tables show metrics, so new metrics need no UI change.
- **Missing is "—"**, never 0.
- **URL holds view state** (selected window, filters) so views can be shared and reloaded; nothing is stored server
  side for views.
- **Accessibility:** keyboard-navigable tables, visible focus, color never the only signal (deltas use icons too).
- **Number formats** follow [formulas.md §11](formulas.md#11-metric-registry-conventions).

## Configuration

Build-time variables (Vite `VITE_*`): `VITE_API_URL`, `VITE_AUTH_DOMAIN`, `VITE_AUTH_CLIENT_ID`, `VITE_AUTH_AUDIENCE`.
Local values come from `.env.local`.

## Deferred UI decisions

The interview sketched a global window picker and a sandbox toggle in the app bar. Both are **per-page design
decisions to make when those milestones start**, not commitments.
