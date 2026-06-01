# Investing AI — Web (React PWA)

Phase 3 frontend: a responsive, installable Progressive Web App that talks to the
Phase 2 FastAPI backend. Runs on desktop and phone; "Add to Home Screen" for an
app-like experience without an app store.

- **Stack:** React 18, Vite 5, TypeScript, Tailwind CSS, TanStack Query, Zustand,
  React Router, lightweight-charts, `vite-plugin-pwa`.
- **Layers:** Presentation (`features/`, `components/`) → ViewModels (`hooks/`) →
  Repositories (`repositories/`) → Networking (`api/client.ts`) → Models (`models/`).

Features: Auth, Markets (search + detail + candlestick chart), Watchlist, Portfolio,
**Recommendations** (full AI committee output — reasons, risks, agent breakdown,
chair rationale), **Alerts** (notifications feed + "Run now"), and Settings.

> The **Alerts** page shows the in-app notification feed; for phone push, configure
> ntfy and/or Telegram on the backend (see `../backend/README.md`) and the hourly
> scheduler delivers high-priority rating changes there.

---

## Prerequisites

- Node.js 20+ and npm (or run everything via Docker — see below).
- The backend running and reachable (see `../backend/README.md`).

## Quick start

```bash
cd web
cp .env.example .env          # set VITE_API_BASE_URL if not the default
npm install
npm run dev                   # http://localhost:5173
```

By default the app calls `http://localhost:8000/api/v1` — start the backend with
`cd ../backend && docker compose up` first, then register an account in the web UI.

### Run via Docker (no local Node)

```bash
cd web
docker run --rm -it -v "$PWD":/app -w /app -p 5173:5173 node:20 \
  sh -c "npm install && npm run dev -- --host"
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Base URL of the backend API, e.g. `http://localhost:8000/api/v1` |

Vite only exposes vars prefixed with `VITE_` to the client.

## Scripts

```bash
npm run dev         # dev server (HMR)
npm run build       # typecheck + production build to dist/
npm run preview     # serve the production build locally
npm run typecheck   # tsc --noEmit
npm run test        # Vitest (unit + component)
```

## Testing

Vitest + Testing Library, jsdom environment. Covered: the API client (token attach,
401→refresh→retry, forced logout on refresh failure), session storage, auth store,
formatters, and key components. Network is always mocked — no backend needed.

```bash
npm run test
# or in Docker:
docker run --rm -v "$PWD":/app -w /app node:20 sh -c "npm install && npm test"
```

## Install as a PWA (phone)

1. Build + serve over HTTPS (or use the dev server on your LAN).
2. On iOS Safari: Share → **Add to Home Screen**. On Android Chrome: **Install app**.
3. Launches full-screen with the app icon; works offline-ish via the service worker.

## Build & deploy

`npm run build` outputs static files to `dist/` (plus a PWA service worker). Host them
anywhere static:

- **Static host / CDN:** Netlify, Vercel, Cloudflare Pages, GitHub Pages, S3+CloudFront.
- **Alongside the backend:** serve `dist/` from any web server / the FastAPI container.
- **Container:** `npm run build` then serve `dist/` with nginx or `vite preview`.

Set `VITE_API_BASE_URL` at build time to your deployed backend URL. Because the app is
an SPA, configure your host to fall back to `index.html` for unknown routes.

## Project layout

```
src/
├── main.tsx            # entry: Query + Router providers
├── router.tsx          # routes + auth guards (RequireAuth / PublicOnly)
├── api/                # client.ts (fetch + JWT + refresh), endpoints, errors
├── models/             # TS types mirroring the API contracts
├── repositories/       # one module per resource, wraps the API client
├── hooks/              # TanStack Query hooks ("ViewModels")
├── services/           # session (token storage)
├── store/              # authStore (Zustand)
├── components/         # ui/ (design system), layout/ (AppShell + nav), charts/
├── features/           # auth, markets, watchlist, portfolio, settings, recommendations
└── lib/                # formatting + helpers
```

## Notes & tradeoffs

- **Auth tokens** are kept in `localStorage` so sessions survive reloads. This is an
  accepted XSS tradeoff for a personal-use tool; a multi-tenant product would use an
  httpOnly refresh cookie + in-memory access token. The API client transparently
  refreshes the access token on `401` and signs out if the refresh fails.
- **Apple Sign-In** is wired on the backend; the web UI ships email/password. Adding
  Apple JS on the web requires a configured Services ID + verified domain — deferred.
- **CORS:** the backend allows all origins by default (dev). Restrict
  `CORS_ORIGINS` in production.

## References

- API contracts: [`../docs/05-api-contracts.md`](../docs/05-api-contracts.md)
- Folder structure & conventions: [`../docs/02-folder-structure.md`](../docs/02-folder-structure.md)
- Roadmap: [`../docs/07-roadmap.md`](../docs/07-roadmap.md)
