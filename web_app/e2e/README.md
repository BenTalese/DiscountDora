# Browser E2E (Playwright) — minimal smoke layer (FU-540)

Drives the real, built SPA against a real Flask backend in a headless browser.

> **SCOPE (owner, 2026-07-20): SMOKE ONLY.** This layer's one job is to catch
> the catastrophic breaks that unit (Vitest, jsdom) and API (pytest) tests
> structurally can't: *does the built SPA bundle boot, route (hash-mode), and
> authenticate?* That's `auth.setup` + `login` + `smoke` — full stop.
>
> The ~22 feature-behaviour specs that briefly lived here (the "verify-campaign
> regression layer") were **deleted 2026-07-20**. They tested things *subject to
> change* and, as an 84-test single-worker suite, were slow (~20 min) and flaky
> (see the retired FU-591) — a maintenance millstone that outweighed their value
> for a solo-maintained, manually-UAT'd app. **Do NOT re-add feature-flow specs
> here.** Verification of features is a **manual once-off drive** (agent or
> owner); durable pins go to backend/Vitest only when they're stable, low-churn
> contracts. See `DORA_VERIFY_TRIAGE.md` (top banner) for the full stance.

## What it covers

- **`fixtures.ts`** — shared `test`/`expect`; injects the app's own
  runtime backend-URL override (P8-10) so the SPA targets the e2e backend
  (`e2e/env.ts`), never the dev one on :5170. **Import from here, not
  '@playwright/test'.**
- **`helpers.ts`** — CSRF-aware `apiMutate`/`apiGet` + `toast` locator. Not
  imported by the current smoke specs; kept as the reference for the CSRF-header
  pattern (FU-197/FU-571) if the smoke layer ever needs to engineer API state.
- **`auth.setup.ts`** — logs in once as the seeded `dora`/`dora` admin and
  saves the session (`e2e/.auth/user.json`) for `smoke`. (Also the standing pin
  that pre-policy 4-char passwords still log in — FU-442.)
- **`login.spec.ts`** — the login form itself, fresh: good creds → dashboard;
  bad creds → visible error.
- **`smoke.spec.ts`** — authenticated navigation to the key routes (via
  `/#/...` — the router is hash-mode; plain paths silently fall back to the
  dashboard): lazy chunk loads, shell renders, title mounts, no uncaught
  errors, no error boundary — plus a real authenticated `/api` handshake.

That's the whole layer. (The seed still creates a "QA Verdict Cheese" fixture
via `DORA_SEED_QA_FIXTURES=true` in the config — a leftover of the deleted
buy-verdict spec; harmless, removable whenever the seed is next touched.)

## Architecture

Single origin. The Flask backend serves both the API (`/api`) and the built
SPA (`/`, from `web_app/dist/spa`), so there's no dev proxy or CORS. Playwright's
`webServer` (see `playwright.config.ts`) boots a **seeded, throwaway** backend on
`:5171` (see `e2e/env.ts` — deliberately NOT the dev backend's :5170, so the
suite can never silently reuse/mutate a live dev database) via `e2e/serve.py` —
which wipes `data/dora.e2e.db` and runs the app in debug+seed mode
(`db.create_all()` + the `dora`/`dora` admin + the QA fixtures; deliberately NOT
migrations, so it sidesteps the FU-549 from-empty migration issue). The built
SPA's env default points at :5170, so `fixtures.ts` injects the runtime URL
override into every context — that's why specs import `test` from
`./fixtures`.

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
