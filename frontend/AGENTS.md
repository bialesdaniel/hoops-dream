# frontend/AGENTS.md: React + TypeScript conventions

Read with the root `AGENTS.md`. Design: `docs/architecture/frontend.md`.
Commands: `make help`.

## Layout

```text
src/
  pages/        one folder per route (e.g., pages/rosters/)
  components/   shared, presentational components
  api/          generated Connect client + TanStack Query hooks
  auth/         Auth0 provider wiring
  gen/          generated from proto/ (git-ignored; run `make gen`)
```

Co-locate tests (`Foo.test.tsx`) and styles with their component.

## Style

- TypeScript `strict`; no `any` (use `unknown` and narrow). ESLint + Prettier
  decide formatting.
- Function components and hooks only. Keep components small; move data fetching
  into hooks in `src/api/`.
- Server state through TanStack Query; UI state in components or the URL. No
  global state library until needed.
- MUI components and the theme for all styling; no hard-coded colors or pixel
  sizes outside the theme.
- Every table that shows metrics builds its columns from the metric catalog.
- Numbers are formatted by one shared helper that follows formulas.md §11;
  missing values render "—".
- Accessibility: semantic elements, labels on inputs, keyboard access, color is
  never the only signal.
- Design for a monitor first (that's the optimized experience), then make sure
  every page is still usable on a phone: check at 390 px wide before calling a
  page done.

## Testing

- Vitest + React Testing Library. Test behavior users see, not internals. Use
  the in-memory Connect transport for API calls; never hit a real API in tests.

## Pre-approved dependencies

`react`, `react-dom`, `react-router`, `@mui/material`, `@mui/icons-material`,
`@emotion/react`, `@emotion/styled`, `material-react-table`, `@mui/x-charts`,
`@mui/x-date-pickers`, `dayjs`, `@tanstack/react-query`, `@connectrpc/connect`,
`@connectrpc/connect-web`, `@bufbuild/protobuf`, `@auth0/auth0-react`, Dev:
`vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `jsdom`,
`@testing-library/react`, `@testing-library/jest-dom`, `@playwright/test`,
`eslint`, `typescript-eslint`, `prettier`, `@bufbuild/protoc-gen-es`. Anything
else: ask first.
