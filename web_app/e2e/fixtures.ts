import { test as base } from '@playwright/test';
import { E2E_BASE_URL } from './env';

// Every spec imports `test`/`expect` from here, not '@playwright/test'.
//
// The one thing this adds: each browser context gets the app's own
// runtime backend-URL override (P8-10, `dora.backendBaseUrl` in
// localStorage) pointed at the e2e backend BEFORE any page script runs.
// Without it the built SPA falls back to its env default —
// `${hostname}:5170/api`, the dev backend's port — and the suite would
// show "Can't reach Dora's brain" (or worse, silently talk to a live dev
// backend if one is running).
export const test = base.extend({
    context: async ({ context }, use) => {
        await context.addInitScript(
            ({ url }) => {
                window.localStorage.setItem('dora.backendBaseUrl', url);
            },
            { url: `${E2E_BASE_URL}/api` },
        );
        await use(context);
    },
});

export { expect } from '@playwright/test';
