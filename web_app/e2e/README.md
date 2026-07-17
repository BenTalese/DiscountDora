# Browser E2E (Playwright) — FU-540 + the verify-campaign regression layer

Drives the real, built SPA against a real Flask backend in a headless
browser. Since 2026-07-17 this layer has a second job beyond the FU-540
smoke: it is **where verified behaviour gets pinned**. The DORA_VERIFY
campaign's close-out rule (see `DORA_VERIFY_TRIAGE.md`) sends every
regression-worthy manual check here once it has passed a live walk — so a
UAT round re-verifies everything previously proven by running this suite,
and human/agent time goes only to *new* checks. One-time confirmations
(copy, layout, subjective calls) are still verified manually and deleted;
this suite stays a curated set of journeys, not a dump of every checkbox.

## What it covers

- **`fixtures.ts`** — shared `test`/`expect`; injects the app's own
  runtime backend-URL override (P8-10) so the SPA targets the e2e backend
  (`e2e/env.ts`), never the dev one on :5170. **Import from here, not
  '@playwright/test'.**
- **`helpers.ts`** — CSRF-aware `apiMutate`/`apiGet` (for engineering test
  state the UI can't create) + the `toast` locator.
- **`auth.setup.ts`** — logs in once as the seeded `dora`/`dora` admin and
  saves the session (`e2e/.auth/user.json`) for the other specs. (Also the
  standing pin that pre-policy 4-char passwords still log in — FU-442.)
- **`login.spec.ts`** — the login form itself, fresh: good creds → dashboard;
  bad creds → visible error.
- **`smoke.spec.ts`** — authenticated navigation to the key routes (via
  `/#/...` — the router is hash-mode; plain paths silently fall back to the
  dashboard): lazy chunk loads, shell renders, title mounts, no uncaught
  errors, no error boundary — plus a real authenticated `/api` handshake.
- **`password-policy.spec.ts`** — FU-442 policy + FU-568 hint-copy pins:
  passphrase hint on register + reset forms, ≥8 length rule, breach-list
  rejection (case-insensitive), letters-only passphrase accepted.
- **`uploads.spec.ts`** — FU-571 pin (chunked upload + inspect with zero
  CSRF 403s — the bug every non-browser suite missed) + FU-545 FileDrop
  behaviour (filled state holds; Remove doesn't reopen the picker).
- **`buy-verdict.spec.ts`** — FU-454 one-tap actions on the overview
  popover + detail card, and the FU-572 pin (the card repaints in place
  after an action, not stale-until-remount). Asserts against the seeded
  QA fixture (below).

## Deterministic QA fixtures

`playwright.config.ts` sets `DORA_SEED_QA_FIXTURES=true`, which makes the
dev seed (`seed_dev_data(qa_fixtures=True)`) create states the specs assert
against but no API can produce — currently **"QA Verdict Cheese"**
(backdated purchases + waste → the oracle's skip/high + mark_stocked
answer). Add new engineered states there, and keep the spec's expected
numbers in sync with the seed block.

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
