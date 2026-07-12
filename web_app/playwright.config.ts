import { defineConfig, devices } from '@playwright/test';
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

const REPO_ROOT = fileURLToPath(new URL('..', import.meta.url));
const DIST_SPA = fileURLToPath(new URL('./dist/spa', import.meta.url));
const PORT = 5170;
const BASE_URL = `http://localhost:${PORT}`;

// System python on this box (the .venv is broken); override for CI/other envs.
const PYTHON = process.env.DORA_E2E_PYTHON ?? 'python';

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
            DORA_ALLOW_DESTRUCTIVE: 'true',
            DORA_DB_PATH: 'data/dora.e2e.db',
            DORA_SPA_DIR: DIST_SPA,
            DORA_API_PORT: String(PORT),
        },
    },
});
