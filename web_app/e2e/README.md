# Browser E2E (Playwright) — FU-540

A **thin browser smoke layer** that drives the real, built SPA against a real
Flask backend in a headless browser. It is a **complement to the manual
`DORA_VERIFY` QA/UAT walks, not a replacement** — it catches the integration
breaks unit/component tests can't (auth cookie flow, routing, CSRF, the real
SPA↔API handshake, the production bundle actually rendering), but it does not
replace a human walking the running app.

## What it covers

- **`auth.setup.ts`** — logs in once as the seeded `dora`/`dora` admin and
  saves the session (`e2e/.auth/user.json`) for the other specs.
- **`login.spec.ts`** — the login form itself, fresh: good creds → dashboard;
  bad creds → visible error.
- **`smoke.spec.ts`** — authenticated navigation to the key routes
  (dashboard / stock / cookbook / meal-plans / shopping-lists): each loads its
  lazy page chunk, renders the app shell, stays authenticated, throws no
  uncaught error, and doesn't hit the render error boundary — plus a real
  authenticated `/api` handshake on the dashboard.

Keep this layer **thin** (a handful of critical journeys). Deep feature
verification stays with the manual walks and the unit/component/e2e-API suites.

## Architecture

Single origin. The Flask backend serves both the API (`/api`) and the built
SPA (`/`, from `web_app/dist/spa`), so there's no dev proxy or CORS. Playwright's
`webServer` (see `playwright.config.ts`) boots a **seeded, throwaway** backend on
`:5170` via `e2e/serve.py` — which wipes `data/dora.e2e.db` and runs the app in
debug+seed mode (`db.create_all()` + the `dora`/`dora` admin; deliberately NOT
migrations, so it sidesteps the FU-549 from-empty migration issue).

## Running it

One-time: install the browser binary.

```bash
cd web_app
npx playwright install chromium
```

Then, from `web_app/`:

```bash
npm run test:e2e        # builds the SPA (quasar build) + runs the suite
npm run test:e2e:ui     # same, interactive UI mode (assumes SPA already built)
npm run test:e2e:only   # skip the build; run against an existing dist/spa
```

`test:e2e` runs `quasar build -m spa` first so `dist/spa` exists for the backend
to serve. The `webServer` starts/stops the backend automatically; set
`reuseExistingServer` behaviour is on locally (start your own backend on :5170
to iterate faster). On a box where `python` isn't the right interpreter, set
`DORA_E2E_PYTHON=/path/to/python`.

## CI

Deferred to the CI re-enable (**FU-405**). When wiring it: install Python deps +
`npx playwright install --with-deps chromium`, then `npm run test:e2e`. The
config already emits the `github` + HTML reporters under `CI`. Pair with the
Postgres matrix (FU-045/FU-405) if you want the smoke run against Postgres too.

## Notes / gotchas

- The suite needs the browser binary (`npx playwright install chromium`) and a
  built SPA — heavier than the Vitest unit layer, hence its own scripts.
- Selectors intentionally lean on stable attributes (`autocomplete`, ARIA
  roles, `.q-layout`) rather than brittle text/CSS, so UI copy tweaks don't
  break the smoke layer.
- The e2e DB (`data/dora.e2e.db`) is throwaway and git-ignored; it's recreated
  every run.
