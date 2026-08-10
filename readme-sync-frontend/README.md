# README Sync — Frontend

## Setup

```bash
npm install
npm run dev
```

The app expects the backend running at `http://127.0.0.1:5000` (configurable via `.env` → `VITE_API_URL`).

## Build

```bash
npm run build
```

## Verified against the real backend

Every API call in `src/api/*.js` was checked line-by-line against the backend's
actual Flask routes and model `to_dict()` output (not against an assumed contract):

- Auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`
  — response uses `access_token` / `refresh_token` / `user` (flask-jwt-extended).
- Repositories: `GET|POST /repositories`, `GET|DELETE /repositories/:id`,
  `PATCH /repositories/:id/sync-mode`, `GET /repositories/:id/commits`,
  `GET /repositories/:id/analyses/latest`.
- README: `GET|PUT /repositories/:id/readme`, `GET /repositories/:id/readme/versions`,
  `GET /repositories/:id/readme/versions/:version_number`,
  `POST /repositories/:id/readme/versions/:version_number/rollback`.
- Pending updates: `GET /repositories/:id/pending-updates[?status=]`,
  `GET /repositories/:id/pending-updates/:id`,
  `POST .../approve` (no body), `POST .../reject` (optional `{reason}`).

## Known backend limitations (intentionally not faked in the UI)

- No endpoint to push the README back to GitHub — no such button exists in the UI.
- No GitHub OAuth connect endpoint — Account Settings shows `github_username`
  read-only; there is no "Connect GitHub" action.
- No dashboard aggregate endpoint — dashboard stats and the global Pending Updates
  page are computed client-side from `GET /repositories` +
  `GET /repositories/:id/pending-updates`, which are real endpoints.
- No repository-add progress reporting — the UI shows a single "Adding
  repository…" loading state, not a fake multi-step progress bar.

## Cinematic entry animation

`/` now plays a one-time animated intro (logo reveal → GitHub → Code → AI →
README flow diagram → tagline → "Get started") before handing off to the real
Login page, built with the animation library already in the project
(Framer Motion — no new dependency added).

- Shown once per browser session (`sessionStorage`), then subsequent visits to
  `/` go straight to `/login`.
- Authenticated users visiting `/` skip straight to `/dashboard`.
- Respects `prefers-reduced-motion` (skips straight to the CTA).
- A "Skip" control is always available.
- The Login page reuses the same animated background for visual continuity
  with the intro.
- The previous marketing landing page (`src/pages/LandingPage.jsx`) is kept in
  the codebase but no longer routed at `/`, per the requested entry flow.
