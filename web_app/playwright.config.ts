import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

// FU-540 — thin browser-E2E smoke layer. A COMPLEMENT to the manual
// DORA_VERIFY QA/UAT walks, not a replacement: it catches the integration
// breaks unit/component tests can't (auth cookie flow, routing, CSRF, the
// real SPA↔API handshake, the built bundle actually rendering).
//
// Architecture — single origin. The Flask backend serves both the API
// (`/api`) and the built SPA (`/`, from web_app/dist/spa), so there's no dev
// proxy / CORS to reason about. `npm run test:e2e` builds the SPA first, then
// Playwright's webServer boots a seeded throwaway backend on :5170.
//
// Requires (one-time): `npx playwright install chromium`. See e2e/README.md.

import { E2E_BASE_URL, E2E_PORT } from './e2e/env';

const REPO_ROOT = fileURLToPath(new URL('..', import.meta.url));
const DIST_SPA = fileURLToPath(new URL('./dist/spa', import.meta.url));
// Port + base URL live in e2e/env.ts (shared with fixtures.ts — see the
// port-isolation rationale there).
const PORT = E2E_PORT;
const BASE_URL = E2E_BASE_URL;

// Prefer the repo venv (verified working 2026-07-17); DORA_E2E_PYTHON
// overrides for CI/other envs, falling back to system `python` if the
// venv doesn't exist.
const VENV_PYTHON = fileURLToPath(new URL(
    process.platform === 'win32'
        ? '../.venv/Scripts/python.exe'
        : '../.venv/bin/python',
    import.meta.url,
));
const PYTHON =
    process.env.DORA_E2E_PYTHON ?? (existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python');

export default defineConfig({
    testDir: './e2e',
    // Keep smoke fast + serial-ish; the seeded backend is a shared singleton.
    fullyParallel: false,
    workers: 1,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
    timeout: 30_000,
    expect: { timeout: 10_000 },

    use: {
        baseURL: BASE_URL,
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        // On a box where `npx playwright install` can't download the bundled
        // browser, drive an already-installed one: `DORA_E2E_CHANNEL=chrome`
        // (or `msedge`). CI leaves it unset and uses the pinned Chromium.
        // Applied at the top level so BOTH the setup + chromium projects use it.
        ...(process.env.DORA_E2E_CHANNEL
            ? { channel: process.env.DORA_E2E_CHANNEL }
            : {}),
    },

    projects: [
        // Logs in once, saves the session cookie for the smoke specs.
        { name: 'setup', testMatch: /auth\.setup\.ts/ },
        {
            name: 'chromium',
            use: {
                ...devices['Desktop Chrome'],
                storageState: 'e2e/.auth/user.json',
            },
            dependencies: ['setup'],
            testIgnore: /auth\.setup\.ts/,
        },
    ],

    // Boots a seeded backend serving the pre-built SPA. `npm run test:e2e`
    // runs `quasar build` first so dist/spa exists.
    webServer: {
        command: `${PYTHON} web_app/e2e/serve.py`,
        cwd: REPO_ROOT,
        url: `${BASE_URL}/api/health`,
        timeout: 180_000,
        reuseExistingServer: !process.env.CI,
        stdout: 'pipe',
        stderr: 'pipe',
        env: {
            DORA_DEBUG: 'true',
            // FU-591 — stay in debug/seed mode but log at WARNING. The
            // per-request DEBUG body-dumps + INFO request lines (each hitting
            // the rotating file handler) dominated backend latency and degraded
            // the long single-worker run into timeouts / browser-closes.
            DORA_LOG_LEVEL: 'WARNING',
            DORA_ALLOW_DESTRUCTIVE: 'true',
            DORA_DB_PATH: 'data/dora.e2e.db',
            DORA_SPA_DIR: DIST_SPA,
            DORA_API_PORT: String(PORT),
            // Fast boot: skip the 500-item FU-388 load (the docstrings always
            // assumed e2e passes 0, but nothing actually set it until now).
            DORA_SEED_BULK_ITEMS: '0',
            // Deterministic QA states the specs assert against (e.g. the
            // buy-verdict fixture) — see seed_dev_data(qa_fixtures=True).
            DORA_SEED_QA_FIXTURES: 'true',
        },
    },
});
